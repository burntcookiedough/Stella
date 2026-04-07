from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import os


@dataclass(slots=True)
class Settings:
    base_dir: Path
    data_dir: Path
    uploads_dir: Path
    duckdb_path: Path
    llm_config_path: Path
    frontend_origin: str
    username: str
    password: str
    jwt_secret: str
    token_ttl_minutes: int
    dev_bypass: bool
    scheduler_enabled: bool


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    base_dir = Path(os.getenv("STELLA_BASE_DIR", Path.cwd()))
    data_dir = Path(os.getenv("STELLA_DATA_DIR", base_dir / "data"))
    uploads_dir = Path(os.getenv("STELLA_UPLOADS_DIR", data_dir / "uploads"))
    duckdb_path = Path(os.getenv("STELLA_DUCKDB_PATH", data_dir / "stella.duckdb"))
    llm_config_path = Path(os.getenv("STELLA_LLM_CONFIG", base_dir / "llm_config.yaml"))

    for directory in (data_dir, uploads_dir, duckdb_path.parent):
        directory.mkdir(parents=True, exist_ok=True)

    return Settings(
        base_dir=base_dir,
        data_dir=data_dir,
        uploads_dir=uploads_dir,
        duckdb_path=duckdb_path,
        llm_config_path=llm_config_path,
        frontend_origin=os.getenv("STELLA_FRONTEND_ORIGIN", "http://127.0.0.1:5173"),
        username=os.getenv("STELLA_USERNAME", "stella"),
        password=os.getenv("STELLA_PASSWORD", "stella"),
        jwt_secret=os.getenv("STELLA_JWT_SECRET", "change-me-in-production"),
        token_ttl_minutes=int(os.getenv("STELLA_TOKEN_TTL_MINUTES", "720")),
        dev_bypass=os.getenv("STELLA_DEV_BYPASS", "true").lower() == "true",
        scheduler_enabled=os.getenv("STELLA_SCHEDULER_ENABLED", "true").lower() == "true",
    )
