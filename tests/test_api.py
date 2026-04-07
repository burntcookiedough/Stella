from __future__ import annotations

from pathlib import Path
import asyncio
import importlib
import os

import httpx


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
