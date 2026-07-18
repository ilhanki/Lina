"""Natural-language and voice routing helpers for explicit Codex requests."""

from dataclasses import dataclass

from lina.codex.intent import classify_codex_intent


@dataclass(frozen=True, slots=True)
class CodexVoiceIntent:
    matched: bool
    requires_confirmation: bool
    request: str


def route_codex_voice(text: str) -> CodexVoiceIntent:
    request = " ".join(text.split())
    matched = classify_codex_intent(request).operational
    return CodexVoiceIntent(matched, matched, request if matched else "")


def confirmation_prompt() -> str:
    return "Codex görevini hazırladım. Çalışma alanını seçtikten sonra planı onaylamanı isteyeceğim."
