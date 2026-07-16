"""Conservative deterministic checks for obvious response corruption."""

from __future__ import annotations

from collections import Counter
import re
import unicodedata

from lina.quality.models import ResponseQualityResult


_ALLOWED_TECHNICAL = frozenset({
    "api", "cli", "gui", "json", "http", "https", "url", "python", "ollama",
    "agent", "model", "prompt", "context", "tool", "provider", "commit", "branch",
    "repository", "release", "tag", "stream", "token", "windows", "pyside",
    "stt", "tts", "microphone", "audio", "vision", "markdown", "unicode",
})
_COMMON_ENGLISH = frozenset({
    "about", "things", "images", "today", "hello", "user", "assistant", "because",
    "with", "this", "that", "what", "your", "have", "from", "into", "some", "edit",
})
_ROLE_PREFIX = re.compile(r"^\s*(?:assistant|asistan|lina|system|sistem|user|kullanıcı)\s*:\s*", re.I)
_BAD_PERSONA = re.compile(r"\b(?:ben\s+sen\s+lina(?:'sın|sın)?|sen\s+lina'sın\s+ben|kullanıcı\s*:|assistant\s*:)", re.I)
_MALFORMED = re.compile(r"\b(?:imagesi|thingsi|editurma|algoritmiler|progressu|today'de|aboutu|tentang)\b", re.I)
_GREETING = re.compile(r"^(?:selam|merhaba|nasılsın|iyi günler)[!,.\s]+", re.I)


class ResponseQualityValidator:
    """Reject only high-confidence defects; this is not a grammar checker."""

    def validate(self, text: str, *, user_text: str = "", expected_language: str = "tr") -> ResponseQualityResult:
        normalized = unicodedata.normalize("NFC", str(text or "")).replace("\x00", "")
        normalized = _ROLE_PREFIX.sub("", normalized.strip())
        normalized = re.sub(r"[ \t]+", " ", normalized)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized).strip()
        words = re.findall(r"[^\W\d_]+(?:['’-][^\W\d_]+)?", normalized.casefold(), re.UNICODE)
        sentences = _sentences(normalized)
        repetition = _repetition_score(sentences, words)
        mixing = _language_mixing_score(words) if expected_language == "tr" else 0.0
        malformed_hits = len(_MALFORMED.findall(normalized))
        persona = bool(_BAD_PERSONA.search(normalized))
        irrelevant_greeting = bool(user_text.strip().endswith("?") and _GREETING.search(normalized) and not _GREETING.search(user_text.strip()))
        punctuation_only = not any(character.isalnum() for character in normalized)
        incomplete = bool(normalized and len(words) > 5 and normalized.endswith(("…", "...", ",", ";", ":", "-")))
        malformed = min(1.0, malformed_hits * 0.45 + persona * 0.7 + irrelevant_greeting * 0.35 + incomplete * 0.35)
        reasons = []
        if not normalized or punctuation_only:
            reasons.append("empty_or_punctuation")
        if repetition >= 0.42:
            reasons.append("repetition")
        if mixing >= 0.28:
            reasons.append("language_mixing")
        if malformed >= 0.45:
            reasons.append("malformed")
        detected = "tr" if expected_language == "tr" and mixing < 0.5 else "mixed" if expected_language == "tr" and mixing else expected_language
        return ResponseQualityResult(
            is_valid=not reasons,
            normalized_text=normalized,
            detected_language=detected,
            language_mixing_score=round(mixing, 3),
            repetition_score=round(repetition, 3),
            malformed_score=round(malformed, 3),
            repair_required=bool(reasons),
            rejection_reason=reasons[0] if reasons else None,
            metrics={
                "character_count": len(normalized), "sentence_count": len(sentences),
                "repetition_detected": repetition >= 0.42,
                "language_category": detected, "malformed_detected": malformed >= 0.45,
            },
        )


def _sentences(text: str) -> list[str]:
    return [" ".join(item.casefold().split()) for item in re.split(r"(?<=[.!?])\s+|\n+", text) if item.strip()]


def _repetition_score(sentences: list[str], words: list[str]) -> float:
    if not sentences and not words:
        return 0.0
    exact = 1.0 - len(set(sentences)) / len(sentences) if sentences else 0.0
    paragraphs = [sentence for sentence in sentences if len(sentence.split()) >= 4]
    near = 0.0
    for index, left in enumerate(paragraphs):
        left_words = set(left.split())
        for right in paragraphs[index + 1:]:
            right_words = set(right.split())
            union = left_words | right_words
            if union and len(left_words & right_words) / len(union) >= 0.82:
                near = max(near, 0.65)
    ngrams = [tuple(words[index:index + 3]) for index in range(max(0, len(words) - 2))]
    repeated_ngrams = sum(count - 1 for count in Counter(ngrams).values() if count > 1)
    ngram_score = min(1.0, repeated_ngrams / max(4, len(ngrams)))
    return max(exact, near, ngram_score)


def _language_mixing_score(words: list[str]) -> float:
    if not words:
        return 0.0
    foreign = sum(word in _COMMON_ENGLISH or _looks_mixed(word) for word in words if word not in _ALLOWED_TECHNICAL)
    return foreign / max(1, len(words))


def _looks_mixed(word: str) -> bool:
    return bool(re.search(r"(?:images|things|about|today|progress)(?:ı|i|u|ü|lar|ler|da|de|dan|den)?$", word))
