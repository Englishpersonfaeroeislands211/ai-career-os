from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal, Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

MessageRole = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class Message:
    role: MessageRole
    content: str


class LLMError(Exception):
    """Raised when an LLM request fails (network, provider, or invalid response)."""


class LLMConfigurationError(LLMError):
    """Raised when the app has no usable AI provider configured."""


class LLMClient(Protocol):
    async def generate_structured(
        self,
        messages: list[Message],
        response_model: type[T],
        *,
        transform_payload: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ) -> T: ...
