from __future__ import annotations

from dataclasses import dataclass

from app.logging_config import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class ToolCallTrace:
    operation: str
    provider: str
    query: str
    latency_ms: float
    result_count: int
    status: str
    error: str | None = None

    def to_log_line(self) -> str:
        parts = [
            f"operation={self.operation}",
            f"provider={self.provider}",
            f'query="{self.query[:80]}"',
            f"latency_ms={self.latency_ms:.0f}",
            f"results={self.result_count}",
            f"status={self.status}",
        ]
        if self.error:
            parts.append(f"error={self.error[:120]}")
        return "tool_call | " + " ".join(parts)


def log_tool_call(trace: ToolCallTrace) -> None:
    if trace.status == "ok":
        logger.info(trace.to_log_line())
    else:
        logger.warning(trace.to_log_line())
