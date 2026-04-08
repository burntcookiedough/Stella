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


def _request_binary(url: str, payload: dict | None = None, headers: dict[str, str] | None = None, timeout: int = 90):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request_headers = {"Accept": "*/*", **(headers or {})}
    if payload is not None:
        request_headers["Content-Type"] = "application/json"
    req = request.Request(url, data=data, headers=request_headers, method="POST")
    with request.urlopen(req, timeout=timeout) as response:
        return response.status, dict(response.headers), response.read()


def _login() -> str:
    _, _, body = _request_json(
        f"{BASE_URL}/v1/auth/login",
        method="POST",
        payload={"username": "stella", "password": "stella"},
    )
    return body["access_token"]


def main() -> None:
    print("Starting Stella backend smoke test...")
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
        text=True,
    )

    try:
        print("Waiting for backend startup...")
        time.sleep(5)

        _, _, healthz = _request_json(f"{BASE_URL}/healthz", timeout=10)
        _, _, readyz = _request_json(f"{BASE_URL}/readyz", timeout=10)
        print("healthz:", healthz)
        print("readyz:", readyz)

        token = _login()
        headers = {"Authorization": f"Bearer {token}"}

        _, _, overview = _request_json(f"{BASE_URL}/v1/overview", headers=headers, timeout=15)
        _, _, correlations = _request_json(f"{BASE_URL}/v1/analytics/correlations", headers=headers, timeout=15)
        report_status, report_headers, report_content = _request_binary(
            f"{BASE_URL}/v1/reports/pdf",
            payload={"source_user_id": None},
            headers=headers,
            timeout=90,
        )

        print("overview latest:", overview.get("latest"))
        print("correlation pairs:", len(correlations.get("pairs", [])))
        print("report status:", report_status, report_headers.get("X-Stella-LLM-Status"))

        if report_status != 200:
            raise RuntimeError("Backend smoke test failed.")
        if not report_content.startswith(b"%PDF"):
            raise RuntimeError("Report endpoint did not return a PDF.")

        print("Backend smoke test passed.")
    finally:
        print("Stopping backend...")
        server_process.terminate()
        server_process.wait()


if __name__ == "__main__":
    main()
