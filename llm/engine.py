from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
import json
import logging
import os

import httpx

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class LLMConfig:
    provider: str
    model: str
    base_url: str
    api_key_env: str | None = None
    temperature: float = 0.2
    max_tokens: int = 512
    timeout_sec: int = 60
    stub_response: str = "Stella stub response."


@dataclass(slots=True)
class LLMHealth:
    provider: str
    model: str
    reachable: bool
    error: str | None = None


class LLMGatewayError(RuntimeError):
    def __init__(self, message: str, *, operation: str, provider: str, model: str) -> None:
        super().__init__(message)
        self.operation = operation
        self.provider = provider
        self.model = model


class LLMGateway:
    def __init__(self, config_path: str | Path = "llm_config.yaml") -> None:
        self.config_path = Path(config_path)
        self.config = load_llm_config(self.config_path)

    def refresh(self) -> None:
        self.config = load_llm_config(self.config_path)

    def health_check(self) -> LLMHealth:
        return _health_check(self.config)

    def chat(self, messages: list[dict[str, str]]) -> str:
        provider = self.config.provider.lower()
        try:
            if provider == "ollama":
                return _ollama_chat(self.config, messages)
            if provider in {"lmstudio", "openai_compat", "llamacpp"}:
                return _openai_compatible_chat(self.config, messages)
            if provider == "stub":
                return _stub_chat(self.config, messages)
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            _raise_gateway_error(self.config, "chat", exc)
        raise ValueError(f"Unsupported LLM provider: {self.config.provider}")

    def stream_chat(self, messages: list[dict[str, str]]) -> Iterable[str]:
        provider = self.config.provider.lower()
        try:
            if provider == "ollama":
                return _ollama_stream(self.config, messages)
            if provider in {"lmstudio", "openai_compat", "llamacpp"}:
                return _openai_compatible_stream(self.config, messages)
            if provider == "stub":
                return _stub_stream(self.config, messages)
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            _raise_gateway_error(self.config, "chat", exc)
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
        stub_response=str(values.get("stub_response", "Stella stub response.")),
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


def _health_check(config: LLMConfig) -> LLMHealth:
    provider = config.provider.lower()
    if provider == "stub":
        return LLMHealth(provider=config.provider, model=config.model, reachable=True)

    try:
        if provider == "ollama":
            response = httpx.get(
                f"{config.base_url}/api/tags",
                headers=_headers(config),
                timeout=config.timeout_sec,
            )
            response.raise_for_status()
            models = response.json().get("models", [])
            if any(_model_matches(config.model, item) for item in models):
                return LLMHealth(provider=config.provider, model=config.model, reachable=True)
            return LLMHealth(
                provider=config.provider,
                model=config.model,
                reachable=False,
                error=f"Configured model '{config.model}' is not available in Ollama.",
            )

        if provider in {"lmstudio", "openai_compat", "llamacpp"}:
            response = httpx.get(
                f"{config.base_url}/v1/models",
                headers=_headers(config),
                timeout=config.timeout_sec,
            )
            response.raise_for_status()
            models = response.json().get("data", [])
            if not models or any(_openai_model_matches(config.model, item) for item in models):
                return LLMHealth(provider=config.provider, model=config.model, reachable=True)
            return LLMHealth(
                provider=config.provider,
                model=config.model,
                reachable=False,
                error=f"Configured model '{config.model}' is not exposed by the provider.",
            )
    except (httpx.HTTPError, json.JSONDecodeError) as exc:
        return LLMHealth(
            provider=config.provider,
            model=config.model,
            reachable=False,
            error=_format_health_error(exc),
        )

    return LLMHealth(
        provider=config.provider,
        model=config.model,
        reachable=False,
        error=f"Unsupported LLM provider: {config.provider}",
    )


def _model_matches(model_name: str, payload: dict[str, Any]) -> bool:
    candidates = [str(payload.get("name", "")), str(payload.get("model", ""))]
    normalized = {candidate.strip() for candidate in candidates if candidate}
    return any(candidate == model_name or candidate.startswith(f"{model_name}:") for candidate in normalized)


def _openai_model_matches(model_name: str, payload: dict[str, Any]) -> bool:
    candidate = str(payload.get("id", "")).strip()
    return bool(candidate) and (candidate == model_name or candidate.startswith(f"{model_name}:"))


def _format_health_error(exc: Exception) -> str:
    if isinstance(exc, httpx.TimeoutException):
        return "Timed out while contacting the configured LLM provider."
    return str(exc)


def _raise_gateway_error(config: LLMConfig, operation: str, exc: Exception) -> None:
    endpoint = _provider_endpoint(config)
    logger.warning(
        "LLM %s failed for provider=%s model=%s timeout_sec=%s endpoint=%s error=%s",
        operation,
        config.provider,
        config.model,
        config.timeout_sec,
        endpoint,
        exc,
    )
    if isinstance(exc, httpx.TimeoutException):
        message = f"{config.provider} timed out while handling {operation}."
    else:
        message = f"{config.provider} is unavailable for {operation}."
    raise LLMGatewayError(
        message,
        operation=operation,
        provider=config.provider,
        model=config.model,
    ) from exc


def _provider_endpoint(config: LLMConfig) -> str:
    provider = config.provider.lower()
    if provider == "ollama":
        return f"{config.base_url}/api/chat"
    if provider in {"lmstudio", "openai_compat", "llamacpp"}:
        return f"{config.base_url}/v1/chat/completions"
    return config.base_url


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


def _stub_chat(config: LLMConfig, _messages: list[dict[str, str]]) -> str:
    return config.stub_response.strip()


def _stub_stream(config: LLMConfig, _messages: list[dict[str, str]]) -> Iterable[str]:
    words = config.stub_response.strip().split()
    for index, word in enumerate(words):
        suffix = "" if index == len(words) - 1 else " "
        yield f"{word}{suffix}"
