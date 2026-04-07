from __future__ import annotations

from pathlib import Path

from llm.engine import LLMGateway, load_llm_config


def test_load_llm_config_reads_yaml_like_file(tmp_path: Path) -> None:
    config_path = tmp_path / "llm_config.yaml"
    config_path.write_text(
        "\n".join(
            [
                "provider: openai_compat",
                "model: local-model",
                "base_url: http://localhost:1234",
                "temperature: 0.5",
                "max_tokens: 256",
                "timeout_sec: 10",
            ]
        ),
        encoding="utf-8",
    )
    config = load_llm_config(config_path)
    assert config.provider == "openai_compat"
    assert config.max_tokens == 256


def test_gateway_refresh_reloads_configuration(tmp_path: Path) -> None:
    config_path = tmp_path / "llm_config.yaml"
    config_path.write_text("provider: ollama\nmodel: first\nbase_url: http://localhost:11434\n", encoding="utf-8")
    gateway = LLMGateway(config_path)
    config_path.write_text("provider: lmstudio\nmodel: second\nbase_url: http://localhost:1234\n", encoding="utf-8")
    gateway.refresh()
    assert gateway.config.provider == "lmstudio"
    assert gateway.config.model == "second"
