from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from urllib import request


BASE_URL = "http://127.0.0.1:8000"
TEMP_DIR = Path(".tmp") / "verify-chat"


def _request_json(url: str, method: str = "GET", payload: dict | None = None, timeout: int = 15):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Accept": "application/json"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    req = request.Request(url, data=data, headers=headers, method=method)
    with request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _login() -> str:
    response = _request_json(
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


def verify_chat() -> None:
    print("Verifying Stella chat websocket...")
    server_process = _ensure_server()

    try:
        token = _login()

        node_script = """
const token = process.argv[1];
const url = `ws://127.0.0.1:8000/v1/chat/ws?token=${token}`;
const socket = new WebSocket(url);
let chunks = "";

socket.addEventListener("open", () => {
  socket.send(JSON.stringify({ message: "Summarize my latest trends." }));
});

socket.addEventListener("message", (event) => {
  const payload = JSON.parse(event.data);
  if (payload.type === "chunk") {
    chunks += payload.content ?? "";
  }
  if (payload.type === "error") {
    console.error(payload.message ?? "chat error");
    process.exit(1);
  }
  if (payload.type === "done") {
    console.log(chunks.trim());
    socket.close();
    process.exit(0);
  }
});

socket.addEventListener("error", () => {
  console.error("websocket error");
  process.exit(1);
});
"""

        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        script_path = TEMP_DIR / "verify_chat.mjs"
        script_path.write_text(node_script, encoding="utf-8")
        result = subprocess.run(
            ["node", str(script_path), token],
            capture_output=True,
            text=True,
            timeout=90,
        )

        print(result.stdout.strip())
        if result.returncode != 0:
            print(result.stderr.strip())
            raise SystemExit(result.returncode)

        print("Chat websocket smoke test passed.")
    finally:
        if server_process is not None:
            server_process.terminate()
            server_process.wait()


if __name__ == "__main__":
    verify_chat()
