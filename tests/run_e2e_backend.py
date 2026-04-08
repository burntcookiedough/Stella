from __future__ import annotations

from pathlib import Path
import os
import shutil
import sys

import uvicorn


ROOT = Path(__file__).resolve().parents[1]
TEMP_DATA_DIR = ROOT / ".tmp" / "e2e-data"
RAW_DIR = TEMP_DATA_DIR / "raw"
FIXTURES_DIR = ROOT / "tests" / "fixtures" / "imports"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def prepare_data_dir() -> None:
    if TEMP_DATA_DIR.exists():
        shutil.rmtree(TEMP_DATA_DIR)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(FIXTURES_DIR / "fitbit_dailyActivity_merged.csv", RAW_DIR / "dailyActivity_merged.csv")
    shutil.copy2(FIXTURES_DIR / "fitbit_sleepDay_merged.csv", RAW_DIR / "sleepDay_merged.csv")


def configure_environment() -> None:
    os.environ["STELLA_BASE_DIR"] = str(ROOT)
    os.environ["STELLA_DATA_DIR"] = str(TEMP_DATA_DIR)
    os.environ["STELLA_UPLOADS_DIR"] = str(TEMP_DATA_DIR / "uploads")
    os.environ["STELLA_DUCKDB_PATH"] = str(TEMP_DATA_DIR / "stella.duckdb")
    os.environ["STELLA_LLM_CONFIG"] = str(ROOT / "tests" / "fixtures" / "llm_stub.yaml")
    os.environ["STELLA_SAMPLE_DATA_DIR"] = str(RAW_DIR)
    os.environ["STELLA_DEV_BYPASS"] = "false"
    os.environ["STELLA_FRONTEND_ORIGIN"] = "http://127.0.0.1:4173"


if __name__ == "__main__":
    prepare_data_dir()
    configure_environment()
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=int(os.environ.get("STELLA_E2E_PORT", "8100")),
    )
