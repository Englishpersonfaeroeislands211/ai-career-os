from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.logging_config import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class LLMCallTrace:
    operation: str
    model: str
    latency_ms: float
    prompt_chars: int
    completion_chars: int
    prompt_tokens: int | None
    completion_tokens: int | None
    status: str
    error: str | None = None

    def to_log_line(self) -> str:
        parts = [
            f"operation={self.operation}",
            f"model={self.model}",
            f"latency_ms={self.latency_ms:.0f}",
            f"prompt_chars={self.prompt_chars}",
            f"completion_chars={self.completion_chars}",
            f"status={self.status}",
        ]
        if self.prompt_tokens is not None:
            parts.append(f"prompt_tokens={self.prompt_tokens}")
        if self.completion_tokens is not None:
            parts.append(f"completion_tokens={self.completion_tokens}")
        if self.error:
            parts.append(f"error={self.error[:120]}")
        return "LLM call | " + " ".join(parts)


def prompt_char_count(messages: list[Any]) -> int:
    return sum(len(getattr(message, "content", "") or "") for message in messages)


def extract_token_usage(payload: dict[str, Any]) -> tuple[int | None, int | None]:
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return None, None
    prompt_tokens = usage.get("prompt_tokens")
    completion_tokens = usage.get("completion_tokens")
    return (
        prompt_tokens if isinstance(prompt_tokens, int) else None,
        completion_tokens if isinstance(completion_tokens, int) else None,
    )


def log_llm_call(trace: LLMCallTrace) -> None:
    if trace.status == "ok":
        logger.info(trace.to_log_line())
    else:
        logger.warning(trace.to_log_line())
