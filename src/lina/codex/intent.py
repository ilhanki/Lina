"""Deterministic operational versus informational Codex intent detection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
import unicodedata


class CodexIntentKind(str, Enum):
    NONE = "none"
    INFORMATIONAL = "informational"
    OPERATIONAL = "operational"


class OperationalCodexIntentError(RuntimeError):
    """Signals that the request must be handled by the bridge, never normal chat."""


@dataclass(frozen=True, slots=True)
class CodexIntentMatch:
    kind: CodexIntentKind
    original_text: str

    @property
    def operational(self) -> bool:
        return self.kind is CodexIntentKind.OPERATIONAL


_NAME = r"(?:codex|kodex|kodeks)"
_TOKEN = re.compile(rf"\b{_NAME}(?:['’]?(?:e|i|le|la|in|den|ten))?\b", re.I)
_INFORMATIONAL = re.compile(
    rf"\b{_NAME}\b.*\b(?:nedir|ne\s+demek|nasıl\s+çalışır|nasil\s+calisir|"
    r"ne\s+işe\s+yarar|ne\s+ise\s+yarar|hakkında\s+bilgi|hakkinda\s+bilgi)\b",
    re.I,
)
_OPERATIONAL = re.compile(
    rf"(?:\b{_NAME}(?:['’]?(?:e|i)|le|['’]le)?\b[^.!?\n]{{0,100}}\b(?:kullan|"
    r"analiz|incele|incelet|geliştir|gelistir|düzelt|duzelt|yaptır|yaptir|"
    r"oku|tara|bak|çalış|calis)|"
    rf"\b{_NAME}\s+(?:görevi|gorevi|geçmişi|gecmisi|ayarları|ayarlari)\b|"
    rf"\b{_NAME}\s+kullanarak\b)",
    re.I,
)
_ACTION = re.compile(
    r"\b(?:kullan(?:arak)?|analiz(?:\s+et)?|incele(?:t)?|geliştir|gelistir|düzelt|duzelt|"
    r"yaptır|yaptir|oku|tara|bak|çalıştır|calistir)\b",
    re.I,
)
_MANAGEMENT = re.compile(
    rf"\b{_NAME}\s+(?:görevi|gorevi|geçmişi|gecmisi|ayarları|ayarlari)\b", re.I
)


def classify_codex_intent(text: str) -> CodexIntentMatch:
    original = " ".join(str(text or "").split())
    normalized = unicodedata.normalize("NFC", original).replace("İ", "i").casefold()
    if not _TOKEN.search(normalized):
        return CodexIntentMatch(CodexIntentKind.NONE, original)
    if _INFORMATIONAL.search(normalized):
        return CodexIntentMatch(CodexIntentKind.INFORMATIONAL, original)
    if _MANAGEMENT.search(normalized) or _ACTION.search(normalized) or _OPERATIONAL.search(normalized):
        return CodexIntentMatch(CodexIntentKind.OPERATIONAL, original)
    return CodexIntentMatch(CodexIntentKind.INFORMATIONAL, original)
