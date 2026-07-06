"""Model provider contract for Lina's Brain."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ModelRequest:
    """Request sent to a model provider."""

    prompt: str


@dataclass(frozen=True)
class ModelResponse:
    """Response returned by a model provider."""

    text: str


class ModelProvider(Protocol):
    """Contract implemented by model providers."""

    def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a model response for the given request."""

