"""Natural-language and voice routing helpers for explicit Codex requests."""

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CodexVoiceIntent:
    matched: bool
    requires_confirmation: bool
    request: str


_CODEX_PATTERN = re.compile(r"\b(?:codex|kodeks)\b", re.IGNORECASE)


def route_codex_voice(text: str) -> CodexVoiceIntent:
    request = " ".join(text.split())
    matched = bool(_CODEX_PATTERN.search(request))
    return CodexVoiceIntent(matched, matched, request if matched else "")


def confirmation_prompt() -> str:
    return "Codex görevini hazırladım. Çalışma alanını seçtikten sonra planı onaylamanı isteyeceğim."

