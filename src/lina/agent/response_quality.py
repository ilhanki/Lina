"""Short Turkish Agent event messages validated before UI persistence or TTS."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from lina.quality.validator import ResponseQualityValidator


class AgentMessageKind(str, Enum):
    PLAN_READY = "plan_ready"
    CLARIFICATION = "clarification"
    APPROVAL = "approval"
    PROGRESS = "progress"
    COMPLETION = "completion"
    PARTIAL = "partial"
    FAILURE = "failure"
    RECOVERY = "recovery"


@dataclass(frozen=True, slots=True)
class AgentMessageResult:
    text: str
    repaired: bool
    rejected: bool


_FALLBACKS = {
    AgentMessageKind.PLAN_READY: "Agent planı hazır. İnceleyip başlatabilirsin.",
    AgentMessageKind.CLARIFICATION: "Görevi başlatmak için bazı bilgiler eksik.",
    AgentMessageKind.APPROVAL: "Bu kalıcı adımı onaylıyor musun?",
    AgentMessageKind.PROGRESS: "Agent görevi güvenli biçimde ilerliyor.",
    AgentMessageKind.COMPLETION: "Görev tamamlandı.",
    AgentMessageKind.PARTIAL: "Görev kısmen tamamlandı.",
    AgentMessageKind.FAILURE: "Görev güvenli biçimde tamamlanamadı.",
    AgentMessageKind.RECOVERY: "Yarım kalan görev otomatik olarak devam ettirilmedi.",
}


class AgentResponseQuality:
    def __init__(self, validator: ResponseQualityValidator | None = None) -> None:
        self.validator = validator or ResponseQualityValidator()

    def prepare(self, text: str, kind: AgentMessageKind | str) -> AgentMessageResult:
        resolved = AgentMessageKind(kind)
        candidate = " ".join(str(text or "").replace("\n", " ").split())[:500]
        quality = self.validator.validate(candidate, user_text="Agent görev durumu", expected_language="tr")
        forbidden = any(term in candidate.casefold() for term in (
            "tool execution", "response verified", "taskı", "progressu", "responseu", "completed status",
        ))
        if quality.is_valid and not forbidden:
            return AgentMessageResult(quality.normalized_text, False, False)
        fallback = _FALLBACKS[resolved]
        fallback_quality = self.validator.validate(fallback, user_text="Agent görev durumu", expected_language="tr")
        if fallback_quality.is_valid:
            return AgentMessageResult(fallback_quality.normalized_text, True, True)
        return AgentMessageResult("Agent görevi güncellendi.", True, True)

    def for_speech(self, text: str, kind: AgentMessageKind | str) -> str:
        prepared = self.prepare(text, kind).text
        first = prepared.split(". ", 1)[0].strip()
        return (first + ".")[:220] if first and not first.endswith((".", "?", "!")) else first[:220]
