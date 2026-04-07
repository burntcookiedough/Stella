from __future__ import annotations

import subprocess
import sys
import time
import json
from urllib import request


BASE_URL = "http://127.0.0.1:8000"


def _request_json(url: str, method: str = "GET", payload: dict | None = None, headers: dict[str, str] | None = None, timeout: int = 15):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request_headers = {"Accept": "application/json", **(headers or {})}
    if payload is not None:
        request_headers["Content-Type"] = "application/json"
    req = request.Request(url, data=data, headers=request_headers, method=method)
    with request.urlopen(req, timeout=timeout) as response:
        body = response.read()
        return response.status, dict(response.headers), json.loads(body.decode("utf-8"))


def _request_binary(url: str, payload: dict | None = None, headers: dict[str, str] | None = None, timeout: int = 120):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request_headers = {"Accept": "*/*", **(headers or {})}
    if payload is not None:
        request_headers["Content-Type"] = "application/json"
    req = request.Request(url, data=data, headers=request_headers, method="POST")
    with request.urlopen(req, timeout=timeout) as response:
        return response.status, dict(response.headers), response.read()


def _login() -> str:
    _, _, response = _request_json(
        f"{BASE_URL}/v1/auth/login",
        method="POST",
        payload={"username": "stella", "password": "stella"},
    )
    return response["access_token"]


def _ensure_server() -> subprocess.Popen[str] | None:
    try:
        _request_json(f"{BASE_URL}/healthz", timeout=2)
        return None
    except Exception:
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
            text=True,
        )
        time.sleep(5)
        return process


def verify_report() -> None:
    print("Verifying Stella PDF report endpoint...")
    server_process = _ensure_server()
    try:
        token = _login()
        response_status, response_headers, response_content = _request_binary(
            f"{BASE_URL}/v1/reports/pdf",
            payload={"source_user_id": None},
            headers={"Authorization": f"Bearer {token}"},
            timeout=120,
        )

        print("status:", response_status)
        print("llm status:", response_headers.get("X-Stella-LLM-Status"))
        print("content-type:", response_headers.get("Content-Type"))

        if response_status != 200:
            raise SystemExit(1)
        if not response_content.startswith(b"%PDF"):
            raise SystemExit("Report endpoint did not return a PDF.")

        print(f"PDF size: {len(response_content)} bytes")
        print("Report endpoint smoke test passed.")
    finally:
        if server_process is not None:
            server_process.terminate()
            server_process.wait()


if __name__ == "__main__":
    verify_report()
