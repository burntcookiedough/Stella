from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import os
import shutil
import sys


@dataclass(slots=True)
class Settings:
    project_dir: Path
    runtime_dir: Path
    data_dir: Path
    uploads_dir: Path
    duckdb_path: Path
    llm_config_path: Path
    sample_data_dir: Path
    frontend_origin: str
    username: str
    password: str
    jwt_secret: str
    token_ttl_minutes: int
    dev_bypass: bool
    scheduler_enabled: bool
    sample_bootstrap_enabled: bool
    require_explicit_auth: bool


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    project_dir = Path(__file__).resolve().parents[1]
    runtime_dir = Path(os.getenv("STELLA_BASE_DIR", _default_runtime_dir()))
    data_dir = Path(os.getenv("STELLA_DATA_DIR", runtime_dir / "data"))
    uploads_dir = Path(os.getenv("STELLA_UPLOADS_DIR", data_dir / "uploads"))
    duckdb_path = Path(os.getenv("STELLA_DUCKDB_PATH", data_dir / "stella.duckdb"))
    llm_config_path = Path(os.getenv("STELLA_LLM_CONFIG", runtime_dir / "llm_config.yaml"))
    sample_data_dir = Path(os.getenv("STELLA_SAMPLE_DATA_DIR", project_dir / "data" / "raw"))
    username = os.getenv("STELLA_USERNAME", "stella")
    password = os.getenv("STELLA_PASSWORD", "stella")
    jwt_secret = os.getenv("STELLA_JWT_SECRET", "change-me-in-production")
    require_explicit_auth = os.getenv("STELLA_REQUIRE_EXPLICIT_AUTH", "false").lower() == "true"

    for directory in (runtime_dir, data_dir, uploads_dir, duckdb_path.parent):
        directory.mkdir(parents=True, exist_ok=True)

    _ensure_default_llm_config(runtime_dir, project_dir, llm_config_path)
    _validate_auth_settings(username, password, jwt_secret, require_explicit_auth)

    return Settings(
        project_dir=project_dir,
        runtime_dir=runtime_dir,
        data_dir=data_dir,
        uploads_dir=uploads_dir,
        duckdb_path=duckdb_path,
        llm_config_path=llm_config_path,
        sample_data_dir=sample_data_dir,
        frontend_origin=os.getenv("STELLA_FRONTEND_ORIGIN", "http://127.0.0.1:5173"),
        username=username,
        password=password,
        jwt_secret=jwt_secret,
        token_ttl_minutes=int(os.getenv("STELLA_TOKEN_TTL_MINUTES", "720")),
        dev_bypass=os.getenv("STELLA_DEV_BYPASS", "true").lower() == "true",
        scheduler_enabled=os.getenv("STELLA_SCHEDULER_ENABLED", "true").lower() == "true",
        sample_bootstrap_enabled=os.getenv("STELLA_ENABLE_SAMPLE_BOOTSTRAP", "false").lower() == "true",
        require_explicit_auth=require_explicit_auth,
    )


def _default_runtime_dir() -> Path:
    if sys.platform == "win32":
        root = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return root / "Stella"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Stella"
    root = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return root / "stella"


def _ensure_default_llm_config(runtime_dir: Path, project_dir: Path, llm_config_path: Path) -> None:
    default_target = runtime_dir / "llm_config.yaml"
    bundled_config = project_dir / "llm_config.yaml"
    if llm_config_path != default_target or llm_config_path.exists() or not bundled_config.exists():
        return
    shutil.copy2(bundled_config, llm_config_path)


def _validate_auth_settings(
    username: str,
    password: str,
    jwt_secret: str,
    require_explicit_auth: bool,
) -> None:
    if not require_explicit_auth:
        return

    weak_passwords = {"", "stella", "changeme", "change-me", "replace-me", "password"}
    weak_secrets = {"", "replace-me", "change-me-in-production", "stella", "password"}
    if username.strip() != "stella":
        raise ValueError("Docker mode requires STELLA_USERNAME=stella for the supported single-user product.")
    if password.strip().lower() in weak_passwords or len(password.strip()) < 12:
        raise ValueError("Docker mode requires a strong STELLA_PASSWORD in the environment.")
    if jwt_secret.strip().lower() in weak_secrets or len(jwt_secret.strip()) < 32:
        raise ValueError("Docker mode requires a strong STELLA_JWT_SECRET in the environment.")
