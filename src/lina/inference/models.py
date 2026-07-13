"""Privacy-safe inference telemetry models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class InferenceStatus(str, Enum):
    SUCCESS = "success"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class InferenceMetrics:
    provider: str
    model: str
    first_token_ms: float | None
    total_ms: float
    prompt_tokens: int | None = None
    generated_tokens: int | None = None
    tokens_per_second: float | None = None
    load_ms: float | None = None
    prompt_evaluation_ms: float | None = None
    generation_ms: float | None = None
    cancelled: bool = False
    error_category: str | None = None

    def __post_init__(self) -> None:
        if self.total_ms < 0:
            raise ValueError("Total duration cannot be negative")


def nanoseconds_to_ms(value: object) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
        return float(value) / 1_000_000
    return None
