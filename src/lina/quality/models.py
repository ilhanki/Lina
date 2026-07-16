"""Typed response-quality results and privacy-safe diagnostics."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ResponseQualityResult:
    is_valid: bool
    normalized_text: str
    detected_language: str
    language_mixing_score: float
    repetition_score: float
    malformed_score: float
    repair_required: bool
    rejection_reason: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ResponseRepairResult:
    text: str
    repaired: bool
    rejected: bool
    quality: ResponseQualityResult
    stale: bool = False
    cancelled: bool = False
