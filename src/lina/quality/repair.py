"""At-most-once response repair without conversation-history disclosure."""

from __future__ import annotations

import logging
from typing import Callable

from lina.quality.models import ResponseRepairResult
from lina.quality.validator import ResponseQualityValidator


SAFE_FALLBACK = "Bu cevabı düzgün biçimde oluşturamadım. Sorunu daha kısa şekilde yeniden deneyebilirsin."
_logger = logging.getLogger("lina.response_quality")


class ResponseRepairService:
    def __init__(self, repair: Callable[[str, str], str] | None = None, validator: ResponseQualityValidator | None = None) -> None:
        self._repair = repair
        self.validator = validator or ResponseQualityValidator()
        self.repair_count = 0
        self.rejection_count = 0

    def accept(self, user_text: str, draft: str, *, request_is_current: Callable[[], bool] | None = None) -> ResponseRepairResult:
        expected_language = "tr" if _looks_turkish(user_text) else "unknown"
        first = self.validator.validate(draft, user_text=user_text, expected_language=expected_language)
        if first.is_valid:
            return ResponseRepairResult(first.normalized_text, False, False, first)
        if request_is_current is not None and not request_is_current():
            return ResponseRepairResult("", False, True, first, stale=True, cancelled=True)
        if self._repair is None:
            self.rejection_count += 1
            return ResponseRepairResult(SAFE_FALLBACK, False, True, first)
        self.repair_count += 1
        try:
            repaired_text = self._repair(user_text[:1000], first.normalized_text[:4000])
        except Exception:
            repaired_text = ""
        second = self.validator.validate(repaired_text, user_text=user_text, expected_language=expected_language)
        if request_is_current is not None and not request_is_current():
            return ResponseRepairResult("", True, True, second, stale=True, cancelled=True)
        if second.is_valid:
            _logger.info("response_quality repaired=true language=%s", second.detected_language)
            return ResponseRepairResult(second.normalized_text, True, False, second)
        self.rejection_count += 1
        _logger.info("response_quality rejected=true reason=%s", second.rejection_reason or "invalid")
        return ResponseRepairResult(SAFE_FALLBACK, True, True, second)


def _looks_turkish(text: str) -> bool:
    normalized = text.casefold()
    if any(character in normalized for character in "çğıöşü"):
        return True
    words = set(normalized.split())
    return bool(words & {"bir", "bu", "ne", "nasıl", "neden", "nedir", "mı", "mi", "ben", "sen", "ve", "için", "bugün"})
