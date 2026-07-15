"""Model provider contract for Lina's Brain."""

from dataclasses import dataclass
from typing import Literal, Protocol

from lina.vision.models import ImageAttachment


ModelRole = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class ModelMessage:
    """A role-bound message sent to a conversational model."""

    role: ModelRole
    content: str


@dataclass(frozen=True)
class ModelRequest:
    """Request sent to a model provider."""

    messages: tuple[ModelMessage, ...]
    image_attachment: ImageAttachment | None = None
    keep_alive: str | int | None = None
    max_output_tokens: int | None = None


@dataclass(frozen=True)
class ModelResponse:
    """Response returned by a model provider."""

    text: str


class ModelProviderError(Exception):
    """Raised when a model provider cannot generate a response."""


class EmptyModelResponseError(ModelProviderError):
    """Raised after one bounded retry still produced no usable final content."""


class ModelProvider(Protocol):
    """Contract implemented by model providers."""

    def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a model response for the given request."""
