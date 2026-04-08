from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
import subprocess
import time

import httpx
import websockets


REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ROOT = "http://127.0.0.1:5173"
BACKEND_READY = "http://127.0.0.1:8000/readyz"
API_ROOT = f"{FRONTEND_ROOT}/api"
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "imports"
ENV_PATH = REPO_ROOT / ".env"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the packaged Stella Docker smoke checks.")
    parser.add_argument(
        "--mode",
        choices=("none", "stub", "all"),
        default="all",
        help="Run degraded-mode smoke, stubbed LLM smoke, or both.",
    )
    return parser.parse_args()


def read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def docker_compose_args(mode: str) -> list[str]:
    args = ["docker", "compose", "-f", "docker-compose.yml"]
    if mode == "stub":
        args.extend(["-f", "docker-compose.smoke.yml"])
    return args


def run_compose(mode: str, *compose_args: str) -> None:
    command = [*docker_compose_args(mode), *compose_args]
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def wait_for_http(url: str, *, timeout_seconds: int = 180) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            response = httpx.get(url, timeout=5.0, trust_env=False)
            if 200 <= response.status_code < 500:
                return
        except httpx.HTTPError:
            time.sleep(1)
            continue
        time.sleep(1)
    raise RuntimeError(f"Timed out waiting for {url}")


async def exercise_chat(token: str, *, expect_success: bool) -> None:
    async with websockets.connect(f"ws://127.0.0.1:5173/ws?token={token}") as websocket:
        await websocket.send(json.dumps({"message": "Summarize the active data set."}))
        chunks: list[str] = []

        while True:
            payload = json.loads(await websocket.recv())
            if payload["type"] == "chunk":
                chunks.append(payload.get("content", ""))
                continue
            if payload["type"] == "done":
                if not expect_success:
                    raise AssertionError("Expected degraded chat mode, but the websocket completed successfully.")
                if not "".join(chunks).strip():
                    raise AssertionError("Chat completed without returning content.")
                return
            if payload["type"] == "error":
                if expect_success:
                    raise AssertionError(f"Expected chat success, but got websocket error: {payload.get('message')}")
                return


def verify_runtime(mode: str) -> None:
    if not ENV_PATH.exists():
        raise FileNotFoundError(f"Missing {ENV_PATH}. Run the Docker launcher first or create the file before smoke.")

    env_values = read_env_file(ENV_PATH)
    username = env_values["STELLA_USERNAME"]
    password = env_values["STELLA_PASSWORD"]

    with httpx.Client(timeout=30.0, trust_env=False) as client:
        wait_for_http(BACKEND_READY)
        wait_for_http(FRONTEND_ROOT)

        frontend_index = client.get(FRONTEND_ROOT)
        assert frontend_index.status_code == 200

        readyz = client.get(f"{API_ROOT}/readyz")
        readyz.raise_for_status()
        ready_payload = readyz.json()
        assert ready_payload["has_data"] is False
        if mode == "none":
            assert ready_payload["llm_reachable"] is False
        else:
            assert ready_payload["llm_reachable"] is True

        login = client.post(
            f"{API_ROOT}/v1/auth/login",
            json={"username": username, "password": password},
        )
        login.raise_for_status()
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        files = [
            ("files", ("dailyActivity_merged.csv", (FIXTURES / "fitbit_dailyActivity_merged.csv").read_bytes(), "text/csv")),
            ("files", ("sleepDay_merged.csv", (FIXTURES / "fitbit_sleepDay_merged.csv").read_bytes(), "text/csv")),
        ]
        import_response = client.post(
            f"{API_ROOT}/v1/imports",
            files=files,
            data={"source": "fitbit"},
            headers=headers,
        )
        import_response.raise_for_status()

        overview = client.get(f"{API_ROOT}/v1/overview", headers=headers)
        overview.raise_for_status()
        overview_payload = overview.json()
        assert overview_payload["latest"] is not None
        assert overview_payload["latest"]["steps"] is not None

        report = client.post(f"{API_ROOT}/v1/reports/pdf", json={"source_user_id": None}, headers=headers)
        report.raise_for_status()
        assert report.content.startswith(b"%PDF")
        if mode == "none":
            assert report.headers["x-stella-llm-status"] == "fallback"
        else:
            assert report.headers["x-stella-llm-status"] == "ok"

        asyncio.run(exercise_chat(token, expect_success=mode == "stub"))


def run_mode(mode: str) -> None:
    print(f"== Stella Docker smoke: {mode} ==")
    try:
        run_compose(mode, "up", "-d", "--build")
        verify_runtime(mode)
    finally:
        run_compose(mode, "down", "-v", "--remove-orphans")


def main() -> None:
    args = parse_args()
    modes = ["none", "stub"] if args.mode == "all" else [args.mode]
    for mode in modes:
        run_mode(mode)


if __name__ == "__main__":
    main()
