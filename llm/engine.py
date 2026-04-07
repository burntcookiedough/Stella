from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
import json
import os

import httpx


@dataclass(slots=True)
class LLMConfig:
    provider: str
    model: str
    base_url: str
    api_key_env: str | None = None
    temperature: float = 0.2
    max_tokens: int = 512
    timeout_sec: int = 60


class LLMGateway:
    def __init__(self, config_path: str | Path = "llm_config.yaml") -> None:
        self.config_path = Path(config_path)
        self.config = load_llm_config(self.config_path)

    def refresh(self) -> None:
        self.config = load_llm_config(self.config_path)

    def chat(self, messages: list[dict[str, str]]) -> str:
        provider = self.config.provider.lower()
        if provider == "ollama":
            return _ollama_chat(self.config, messages)
        if provider in {"lmstudio", "openai_compat", "llamacpp"}:
            return _openai_compatible_chat(self.config, messages)
        raise ValueError(f"Unsupported LLM provider: {self.config.provider}")

    def stream_chat(self, messages: list[dict[str, str]]) -> Iterable[str]:
        provider = self.config.provider.lower()
        if provider == "ollama":
            return _ollama_stream(self.config, messages)
        if provider in {"lmstudio", "openai_compat", "llamacpp"}:
            return _openai_compatible_stream(self.config, messages)
        raise ValueError(f"Unsupported LLM provider: {self.config.provider}")

    def analyze_health_data(self, summary: dict[str, Any]) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are Stella, a privacy-first health intelligence assistant. "
                    "Interpret wearable and health trends without giving medical diagnoses. "
                    "Focus on behavioral insights, risk factors, and next-step observations."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Summarize this health snapshot in under 160 words with a status line, "
                    "2 short findings, and 2 next-step suggestions.\n"
                    f"{json.dumps(summary, indent=2)}"
                ),
            },
        ]
        return self.chat(messages)


def load_llm_config(config_path: str | Path) -> LLMConfig:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Missing LLM config file: {path}")
    values = _parse_yaml_like(path.read_text(encoding="utf-8"))
    return LLMConfig(
        provider=str(values.get("provider", "ollama")),
        model=str(values.get("model", "mistral")),
        base_url=str(values.get("base_url", "http://localhost:11434")).rstrip("/"),
        api_key_env=values.get("api_key_env") or None,
        temperature=float(values.get("temperature", 0.2)),
        max_tokens=int(values.get("max_tokens", 512)),
        timeout_sec=int(values.get("timeout_sec", 60)),
    )


def _parse_yaml_like(raw_text: str) -> dict[str, Any]:
    try:
        import yaml  # type: ignore

        return yaml.safe_load(raw_text) or {}
    except ImportError:
        values: dict[str, Any] = {}
        for line in raw_text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or ":" not in stripped:
                continue
            key, raw_value = stripped.split(":", 1)
            value = raw_value.strip()
            if value in {"", "null", "None"}:
                values[key.strip()] = None
            elif value.lower() in {"true", "false"}:
                values[key.strip()] = value.lower() == "true"
            else:
                try:
                    if "." in value:
                        values[key.strip()] = float(value)
                    else:
                        values[key.strip()] = int(value)
                except ValueError:
                    values[key.strip()] = value
        return values


def _headers(config: LLMConfig) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if config.api_key_env:
        api_key = os.getenv(config.api_key_env, "")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _ollama_chat(config: LLMConfig, messages: list[dict[str, str]]) -> str:
    response = httpx.post(
        f"{config.base_url}/api/chat",
        json={"model": config.model, "messages": messages, "stream": False},
        headers=_headers(config),
        timeout=config.timeout_sec,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("message", {}).get("content", "").strip()


def _ollama_stream(config: LLMConfig, messages: list[dict[str, str]]) -> Iterable[str]:
    with httpx.stream(
        "POST",
        f"{config.base_url}/api/chat",
        json={"model": config.model, "messages": messages, "stream": True},
        headers=_headers(config),
        timeout=config.timeout_sec,
    ) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line:
                continue
            payload = json.loads(line)
            chunk = payload.get("message", {}).get("content", "")
            if chunk:
                yield chunk


def _openai_compatible_chat(config: LLMConfig, messages: list[dict[str, str]]) -> str:
    response = httpx.post(
        f"{config.base_url}/v1/chat/completions",
        json={
            "model": config.model,
            "messages": messages,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "stream": False,
        },
        headers=_headers(config),
        timeout=config.timeout_sec,
    )
    response.raise_for_status()
    payload = response.json()
    choices = payload.get("choices", [])
    if not choices:
        return ""
    return choices[0].get("message", {}).get("content", "").strip()


def _openai_compatible_stream(config: LLMConfig, messages: list[dict[str, str]]) -> Iterable[str]:
    with httpx.stream(
        "POST",
        f"{config.base_url}/v1/chat/completions",
        json={
            "model": config.model,
            "messages": messages,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "stream": True,
        },
        headers=_headers(config),
        timeout=config.timeout_sec,
    ) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line or not line.startswith("data: "):
                continue
            payload_text = line[6:].strip()
            if payload_text == "[DONE]":
                break
            payload = json.loads(payload_text)
            delta = payload.get("choices", [{}])[0].get("delta", {}).get("content", "")
            if delta:
                yield delta
