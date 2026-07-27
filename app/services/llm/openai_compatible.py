from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.logging_config import get_logger
from app.services.llm.base import LLMError, Message
from app.services.llm.urls import normalize_openai_base_url

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

DEFAULT_TIMEOUT = 120.0


@dataclass(frozen=True)
class OpenAICompatibleConfig:
    model: str
    base_url: str
    api_key: str | None = None


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
    ) -> T:
        payload = self._build_payload(messages, response_model)
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

        content = self._extract_message_content(response.json())
        return self._parse_structured_response(
            content,
            response_model,
            transform_payload=transform_payload,
        )

    def _build_payload(
        self,
        messages: list[Message],
        response_model: type[T],
    ) -> dict[str, Any]:
        schema_name = _schema_name(response_model)
        schema = response_model.model_json_schema()

        return {
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

    def _extract_message_content(self, payload: dict[str, Any]) -> str:
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise LLMError("Provider returned no completion choices.")

        message = choices[0].get("message", {})
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise LLMError("Provider returned an empty completion.")
        return content.strip()

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


def _schema_name(model: type[BaseModel]) -> str:
    name = model.__name__
    return "".join(ch if ch.isalnum() else "_" for ch in name).strip("_").lower() or "response"


def build_openai_compatible_config(
    *,
    model: str,
    base_url: str | None,
    api_key: str | None,
    default_base_url: str | None = None,
) -> OpenAICompatibleConfig:
    resolved_base = base_url or default_base_url or "https://api.openai.com/v1"
    return OpenAICompatibleConfig(
        model=model,
        base_url=normalize_openai_base_url(resolved_base),
        api_key=api_key,
    )
