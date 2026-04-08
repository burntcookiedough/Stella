from __future__ import annotations

from pathlib import Path
import importlib


def test_default_runtime_dir_copies_llm_config(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("STELLA_BASE_DIR", str(tmp_path))
    monkeypatch.delenv("STELLA_LLM_CONFIG", raising=False)
    monkeypatch.delenv("STELLA_DATA_DIR", raising=False)
    monkeypatch.delenv("STELLA_UPLOADS_DIR", raising=False)
    monkeypatch.delenv("STELLA_DUCKDB_PATH", raising=False)
    monkeypatch.delenv("STELLA_SAMPLE_DATA_DIR", raising=False)

    import backend.config

    backend.config.get_settings.cache_clear()
    importlib.reload(backend.config)

    settings = backend.config.get_settings()

    assert settings.runtime_dir == tmp_path
    assert settings.data_dir == tmp_path / "data"
    assert settings.uploads_dir == tmp_path / "data" / "uploads"
    assert settings.duckdb_path == tmp_path / "data" / "stella.duckdb"
    assert settings.llm_config_path == tmp_path / "llm_config.yaml"
    assert settings.llm_config_path.exists()
    assert "provider:" in settings.llm_config_path.read_text(encoding="utf-8")


def test_explicit_auth_mode_rejects_weak_defaults(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("STELLA_BASE_DIR", str(tmp_path))
    monkeypatch.delenv("STELLA_LLM_CONFIG", raising=False)
    monkeypatch.setenv("STELLA_REQUIRE_EXPLICIT_AUTH", "true")
    monkeypatch.setenv("STELLA_USERNAME", "stella")
    monkeypatch.setenv("STELLA_PASSWORD", "stella")
    monkeypatch.setenv("STELLA_JWT_SECRET", "replace-me")

    import backend.config

    backend.config.get_settings.cache_clear()
    importlib.reload(backend.config)

    try:
        backend.config.get_settings()
        raise AssertionError("Expected Docker-style explicit auth validation to reject weak defaults.")
    except ValueError as exc:
        assert "strong STELLA_PASSWORD" in str(exc)
