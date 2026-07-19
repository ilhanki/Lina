"""Natural-language and voice routing helpers for explicit Codex requests."""

from dataclasses import dataclass
from enum import Enum
import re

from lina.codex.intent import classify_codex_intent


@dataclass(frozen=True, slots=True)
class CodexVoiceIntent:
    matched: bool
    requires_confirmation: bool
    request: str


class CodexControlAction(str, Enum):
    NONE = "none"
    STATUS = "status"
    STOP = "stop"
    RESUME = "resume"
    SHOW_CHANGES = "show_changes"


@dataclass(frozen=True, slots=True)
class CodexControlIntent:
    action: CodexControlAction

    @property
    def matched(self) -> bool:
        return self.action is not CodexControlAction.NONE


def route_codex_voice(text: str) -> CodexVoiceIntent:
    request = " ".join(text.split())
    matched = classify_codex_intent(request).operational
    return CodexVoiceIntent(matched, matched, request if matched else "")


def confirmation_prompt() -> str:
    return (
        "Codex görevini hazırladım. Çalışma alanını seçtikten sonra planı "
        "onaylamanı isteyeceğim."
    )


def route_codex_control(text: str) -> CodexControlIntent:
    normalized = " ".join(str(text or "").casefold().split())
    if not re.search(r"\b(?:codex|kodex|kodeks)\b", normalized):
        return CodexControlIntent(CodexControlAction.NONE)
    if re.search(r"\b(?:durdur|iptal et|stop)\b", normalized):
        return CodexControlIntent(CodexControlAction.STOP)
    if re.search(r"\b(?:devam et|sürdür|resume)\b", normalized):
        return CodexControlIntent(CodexControlAction.RESUME)
    if re.search(r"\b(?:değişiklikleri göster|diff(?:i)? göster|inceleme(?:yi)? aç)\b", normalized):
        return CodexControlIntent(CodexControlAction.SHOW_CHANGES)
    if re.search(r"\b(?:durum(?:u|unu)?|ne yapıyor|ilerleme)\b", normalized):
        return CodexControlIntent(CodexControlAction.STATUS)
    return CodexControlIntent(CodexControlAction.NONE)
