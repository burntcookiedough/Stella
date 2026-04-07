from __future__ import annotations

from pathlib import Path
import asyncio
import importlib
import os

import httpx
from starlette.websockets import WebSocketDisconnect, WebSocketState

from llm.engine import LLMGatewayError, LLMHealth


FIXTURES = Path(__file__).parent / "fixtures" / "imports"


def _app(tmp_path: Path):
    os.environ["STELLA_BASE_DIR"] = str(tmp_path)
    os.environ["STELLA_DATA_DIR"] = str(tmp_path / "data")
    os.environ["STELLA_UPLOADS_DIR"] = str(tmp_path / "data" / "uploads")
    os.environ["STELLA_DUCKDB_PATH"] = str(tmp_path / "data" / "stella.duckdb")
    os.environ["STELLA_LLM_CONFIG"] = str(tmp_path / "llm_config.yaml")
    os.environ["STELLA_DEV_BYPASS"] = "true"
    (tmp_path / "llm_config.yaml").write_text(
        "provider: ollama\nmodel: mistral\nbase_url: http://localhost:11434\n",
        encoding="utf-8",
    )

    import backend.config
    import backend.main

    backend.config.get_settings.cache_clear()
    importlib.reload(backend.config)
    importlib.reload(backend.main)
    return backend.main


async def _async_client(module):
    await module.startup_event()
    transport = httpx.ASGITransport(app=module.app)
    client = httpx.AsyncClient(transport=transport, base_url="http://testserver")
    return client


class _FakeClient:
    host = "127.0.0.1"


class FakeWebSocket:
    def __init__(self, app, incoming_messages: list[dict[str, object] | Exception]):
        self.app = app
        self.query_params: dict[str, str] = {}
        self.client = _FakeClient()
        self.application_state = WebSocketState.CONNECTING
        self.client_state = WebSocketState.CONNECTED
        self._incoming_messages = incoming_messages
        self._index = 0
        self.accepted = False
        self.sent_messages: list[dict[str, object]] = []
        self.closed_code: int | None = None
        self.disconnect_after_first_send = False

    async def accept(self) -> None:
        self.accepted = True
        self.application_state = WebSocketState.CONNECTED

    async def receive_json(self) -> dict[str, object]:
        if self._index >= len(self._incoming_messages):
            raise WebSocketDisconnect(1000)
        item = self._incoming_messages[self._index]
        self._index += 1
        if isinstance(item, Exception):
            self.client_state = WebSocketState.DISCONNECTED
            raise item
        return item

    async def send_json(self, payload: dict[str, object]) -> None:
        if self.application_state != WebSocketState.CONNECTED:
            raise RuntimeError("socket closed")
        self.sent_messages.append(payload)
        if self.disconnect_after_first_send:
            self.application_state = WebSocketState.DISCONNECTED
            self.client_state = WebSocketState.DISCONNECTED

    async def close(self, code: int = 1000) -> None:
        self.closed_code = code
        self.application_state = WebSocketState.DISCONNECTED
        self.client_state = WebSocketState.DISCONNECTED


def test_import_overview_and_correlations(tmp_path: Path) -> None:
    module = _app(tmp_path)

    async def run() -> None:
        client = await _async_client(module)
        login_response = await client.post("/v1/auth/login", json={"username": "stella", "password": "stella"})
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            "/v1/imports",
            files=[
                ("files", ("dailyActivity_merged.csv", (FIXTURES / "fitbit_dailyActivity_merged.csv").read_bytes(), "text/csv")),
                ("files", ("sleepDay_merged.csv", (FIXTURES / "fitbit_sleepDay_merged.csv").read_bytes(), "text/csv")),
            ],
            data={"source": "fitbit"},
            headers=headers,
        )
        assert response.status_code == 200

        overview = await client.get("/v1/overview", headers=headers)
        assert overview.status_code == 200
        assert overview.json()["latest"]["steps"] is not None

        correlations = await client.get("/v1/analytics/correlations", headers=headers)
        assert correlations.status_code == 200
        assert "pairs" in correlations.json()

        await client.aclose()
        await module.shutdown_event()

    asyncio.run(run())

def test_login_returns_token(tmp_path: Path) -> None:
    module = _app(tmp_path)

    async def run() -> None:
        client = await _async_client(module)
        response = await client.post("/v1/auth/login", json={"username": "stella", "password": "stella"})
        assert response.status_code == 200
        assert response.json()["access_token"]

        await client.aclose()
        await module.shutdown_event()

    asyncio.run(run())


def test_login_rejects_invalid_credentials(tmp_path: Path) -> None:
    module = _app(tmp_path)

    async def run() -> None:
        client = await _async_client(module)
        response = await client.post("/v1/auth/login", json={"username": "stella", "password": "wrong"})
        assert response.status_code == 401

        await client.aclose()
        await module.shutdown_event()

    asyncio.run(run())


def test_readyz_includes_llm_diagnostics(tmp_path: Path) -> None:
    module = _app(tmp_path)

    async def run() -> None:
        client = await _async_client(module)
        module.app.state.llm_gateway.health_check = lambda: LLMHealth(
            provider="stub",
            model="test-model",
            reachable=False,
            error="provider unavailable",
        )

        response = await client.get("/readyz")
        assert response.status_code == 200
        assert response.json() == {
            "status": "ready",
            "has_data": False,
            "llm_provider": "stub",
            "llm_model": "test-model",
            "llm_reachable": False,
            "llm_error": "provider unavailable",
        }

        await client.aclose()
        await module.shutdown_event()

    asyncio.run(run())


def test_report_falls_back_when_llm_fails(tmp_path: Path) -> None:
    module = _app(tmp_path)

    async def run() -> None:
        client = await _async_client(module)
        module.app.state.llm_gateway.analyze_health_data = lambda _summary: (_ for _ in ()).throw(
            LLMGatewayError(
                "ollama timed out while handling report_summary.",
                operation="report_summary",
                provider="ollama",
                model="mistral",
            )
        )

        login_response = await client.post("/v1/auth/login", json={"username": "stella", "password": "stella"})
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        import_response = await client.post(
            "/v1/imports",
            files=[
                ("files", ("dailyActivity_merged.csv", (FIXTURES / "fitbit_dailyActivity_merged.csv").read_bytes(), "text/csv")),
                ("files", ("sleepDay_merged.csv", (FIXTURES / "fitbit_sleepDay_merged.csv").read_bytes(), "text/csv")),
            ],
            data={"source": "fitbit"},
            headers=headers,
        )
        assert import_response.status_code == 200

        response = await client.post("/v1/reports/pdf", json={"source_user_id": None}, headers=headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.headers["x-stella-llm-status"] == "fallback"
        assert "timed out" in response.headers["x-stella-llm-error"]
        assert response.content.startswith(b"%PDF")

        await client.aclose()
        await module.shutdown_event()

    asyncio.run(run())


def test_chat_websocket_disconnect_is_clean(tmp_path: Path) -> None:
    module = _app(tmp_path)
    asyncio.run(module.startup_event())
    websocket = FakeWebSocket(module.app, [WebSocketDisconnect(1001)])
    asyncio.run(module.chat_socket(websocket))
    assert websocket.accepted is True
    assert websocket.sent_messages == []
    asyncio.run(module.shutdown_event())


def test_chat_streaming_disconnect_does_not_crash(tmp_path: Path) -> None:
    module = _app(tmp_path)

    def streaming_messages(_messages):
        yield "chunk one "
        yield "chunk two"

    asyncio.run(module.startup_event())
    module.app.state.llm_gateway.stream_chat = streaming_messages
    websocket = FakeWebSocket(module.app, [{"message": "hello"}])
    websocket.disconnect_after_first_send = True

    asyncio.run(module.chat_socket(websocket))

    assert websocket.sent_messages == [{"type": "chunk", "content": "chunk one "}]
    assert websocket.closed_code is None
    asyncio.run(module.shutdown_event())


def test_chat_provider_error_returns_error_frame(tmp_path: Path) -> None:
    module = _app(tmp_path)

    def broken_stream(_messages):
        raise LLMGatewayError(
            "stub is unavailable for chat.",
            operation="chat",
            provider="stub",
            model="stub-model",
        )
        yield ""

    asyncio.run(module.startup_event())
    module.app.state.llm_gateway.stream_chat = broken_stream
    websocket = FakeWebSocket(module.app, [{"message": "hello"}])

    asyncio.run(module.chat_socket(websocket))

    assert websocket.sent_messages == [{"type": "error", "message": "stub is unavailable for chat."}]
    assert websocket.closed_code == 1011
    asyncio.run(module.shutdown_event())
