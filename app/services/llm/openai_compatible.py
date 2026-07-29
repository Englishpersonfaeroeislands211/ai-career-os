from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.logging_config import get_logger
from app.services.llm.base import LLMError, Message
from app.services.llm.tracing import (
    LLMCallTrace,
    extract_token_usage,
    log_llm_call,
    prompt_char_count,
)
from app.services.llm.urls import normalize_openai_base_url

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

DEFAULT_TIMEOUT = 120.0
NVIDIA_HOST = "integrate.api.nvidia.com"
REASONING_MODEL_MARKERS = ("nemotron", "gpt-oss", "deepseek-r1")
REASONING_MIN_MAX_TOKENS = 4096


@dataclass(frozen=True)
class OpenAICompatibleConfig:
    model: str
    base_url: str
    api_key: str | None = None
    provider: str | None = None


class OpenAICompatibleClient:
    """Chat completions client for OpenAI and OpenAI-compatible providers."""

    def __init__(
        self,
        config: OpenAICompatibleConfig,
        *,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._config = config
        self._http_client = http_client
        self._owns_client = http_client is None

    async def generate_structured(
        self,
        messages: list[Message],
        response_model: type[T],
        *,
        transform_payload: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
        max_tokens: int | None = None,
    ) -> T:
        operation = response_model.__name__
        prompt_chars = prompt_char_count(messages)
        started = time.perf_counter()

        try:
            payload = self._build_payload(messages, response_model, max_tokens=max_tokens)
            url = f"{self._config.base_url.rstrip('/')}/chat/completions"
            headers = {"Content-Type": "application/json"}
            if self._config.api_key:
                headers["Authorization"] = f"Bearer {self._config.api_key}"

            client = self._http_client or httpx.AsyncClient(timeout=DEFAULT_TIMEOUT)
            try:
                response = await client.post(url, headers=headers, json=payload)
            except httpx.ConnectError as exc:
                raise LLMError(
                    f"Could not connect to {self._config.base_url}. Is the server running?"
                ) from exc
            except httpx.TimeoutException as exc:
                raise LLMError(f"Timed out waiting for {self._config.base_url}.") from exc
            finally:
                if self._owns_client and self._http_client is None:
                    await client.aclose()

            if response.status_code >= 400:
                raise LLMError(f"Provider returned {response.status_code}: {response.text[:300]}")

            response_payload = response.json()
            content = self._extract_message_content(response_payload)
            prompt_tokens, completion_tokens = extract_token_usage(response_payload)
            result = self._parse_structured_response(
                content,
                response_model,
                transform_payload=transform_payload,
            )
        except LLMError as exc:
            log_llm_call(
                LLMCallTrace(
                    operation=operation,
                    model=self._config.model,
                    latency_ms=(time.perf_counter() - started) * 1000,
                    prompt_chars=prompt_chars,
                    completion_chars=0,
                    prompt_tokens=None,
                    completion_tokens=None,
                    status="error",
                    error=str(exc),
                )
            )
            raise

        log_llm_call(
            LLMCallTrace(
                operation=operation,
                model=self._config.model,
                latency_ms=(time.perf_counter() - started) * 1000,
                prompt_chars=prompt_chars,
                completion_chars=len(content),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                status="ok",
            )
        )
        return result

    def _build_payload(
        self,
        messages: list[Message],
        response_model: type[T],
        *,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        schema_name = _schema_name(response_model)
        schema = response_model.model_json_schema()

        payload: dict[str, Any] = {
            "model": self._config.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "schema": schema,
                    "strict": False,
                },
            },
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        _apply_provider_payload_options(payload, self._config)
        return payload

    def _extract_message_content(self, payload: dict[str, Any]) -> str:
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise LLMError("Provider returned no completion choices.")

        choice = choices[0]
        message = choice.get("message", {})
        content = normalize_message_content(message.get("content"))
        if content:
            return content

        # Some providers return JSON in alternate reasoning fields when misconfigured.
        for key in ("reasoning_content", "reasoning"):
            alternate = normalize_message_content(message.get(key))
            if alternate and alternate.lstrip().startswith("{"):
                return alternate

        finish_reason = choice.get("finish_reason")
        usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
        completion_tokens = usage.get("completion_tokens")
        raise LLMError(
            "Provider returned an empty completion "
            f"(finish_reason={finish_reason!r}, completion_tokens={completion_tokens}). "
            "Reasoning models (Nemotron, gpt-oss) often exhaust max_tokens during "
            "thinking — use max_tokens>=4096 or a non-reasoning model such as "
            "meta/llama-3.3-70b-instruct."
        )

    def _parse_structured_response(
        self,
        content: str,
        response_model: type[T],
        *,
        transform_payload: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ) -> T:
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise LLMError(f"Provider returned invalid JSON: {content[:200]}") from exc

        if not isinstance(data, dict):
            raise LLMError("Provider returned JSON that is not an object.")

        if transform_payload is not None:
            data = transform_payload(data)

        try:
            return response_model.model_validate(data)
        except ValidationError as exc:
            raise LLMError(f"Response did not match schema: {exc}") from exc


def normalize_message_content(content: Any) -> str | None:
    """Normalize OpenAI-style message content to plain text."""
    if isinstance(content, str):
        stripped = content.strip()
        return stripped or None
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if not isinstance(part, dict):
                continue
            if part.get("type") == "text":
                text = part.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text.strip())
        if parts:
            return "\n".join(parts)
    return None


def is_reasoning_model(model: str) -> bool:
    lower = model.lower()
    return any(marker in lower for marker in REASONING_MODEL_MARKERS)


def is_nvidia_host(base_url: str, provider: str | None) -> bool:
    return provider == "nvidia" or NVIDIA_HOST in base_url


def _apply_provider_payload_options(
    payload: dict[str, Any],
    config: OpenAICompatibleConfig,
) -> None:
    """Tune requests for NVIDIA reasoning models that hide answers in thinking tokens."""
    reasoning = is_reasoning_model(config.model)
    nvidia = is_nvidia_host(config.base_url, config.provider)

    if reasoning:
        payload["chat_template_kwargs"] = {"enable_thinking": False}
        current = payload.get("max_tokens")
        if current is None:
            payload["max_tokens"] = REASONING_MIN_MAX_TOKENS
        else:
            payload["max_tokens"] = max(int(current), REASONING_MIN_MAX_TOKENS)
    elif nvidia and payload.get("max_tokens") is not None:
        payload["max_tokens"] = max(int(payload["max_tokens"]), 2048)


def _schema_name(model: type[BaseModel]) -> str:
    name = model.__name__
    return "".join(ch if ch.isalnum() else "_" for ch in name).strip("_").lower() or "response"


def build_openai_compatible_config(
    *,
    model: str,
    base_url: str | None,
    api_key: str | None,
    default_base_url: str | None = None,
    provider: str | None = None,
) -> OpenAICompatibleConfig:
    resolved_base = base_url or default_base_url or "https://api.openai.com/v1"
    return OpenAICompatibleConfig(
        model=model,
        base_url=normalize_openai_base_url(resolved_base),
        api_key=api_key,
        provider=provider,
    )
