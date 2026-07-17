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
    "framework", "git", "github", "pyside6", "llama", "gemma", "mistral",
})
_COMMON_ENGLISH = frozenset({
    "about", "things", "images", "today", "hello", "user", "assistant", "because",
    "with", "this", "that", "what", "your", "have", "from", "into", "some", "edit",
})
_COMMON_FOREIGN = frozenset({
    "và", "của", "một", "không", "trong", "được", "những", "tôi", "bạn",
    "bonjour", "merci", "avec", "pour", "dans", "und", "nicht", "aber",
    "hola", "gracias", "para", "pero",
})
_ROLE_PREFIX = re.compile(r"^\s*(?:assistant|asistan|lina|system|sistem|user|kullanıcı)\s*:\s*", re.I)
_BAD_PERSONA = re.compile(r"\b(?:ben\s+sen\s+lina(?:'sın|sın)?|sen\s+lina'sın\s+ben|kullanıcı\s*:|assistant\s*:)", re.I)
_MALFORMED = re.compile(
    r"\b(?:imagesi|thingsi|editurma|algoritmiler|progressu|today'de|aboutu|tentang|"
    r"responseu|taskı|fileı|chatte|memoryyi|toolu|providerı|contexti|promptu|streami|tokeni)\b",
    re.I,
)
_GREETING = re.compile(r"^(?:(?:sen\s+)?nasılsın|selam|merhaba|iyi günler)[!,.\s]+", re.I)
_FOREIGN_PHRASE = re.compile(r"\b(?:xin chào|trí tuệ nhân tạo|cảm ơn|je suis|por favor|guten tag)\b", re.I)
_GENERIC_HELP = re.compile(
    r"\b(?:nasıl yardımcı olabilirim|yardımcı olmaktan memnuniyet duyarım|ne yapmak istersin|ne yapalım)\b",
    re.I,
)
_GENERIC_CLOSING = re.compile(r"\b(?:umarım yardımcı olmuştur|başka bir sorun olursa sorabilirsin)\b", re.I)
_META_LEAK = re.compile(
    r"(?:<\|(?:system|assistant|user|end)_?\|>|\b(?:system prompt|developer message|"
    r"as an ai language model|internal instruction|chain of thought)\s*:?)",
    re.I,
)


class ResponseQualityValidator:
    """Reject only high-confidence defects; this is not a grammar checker."""

    def validate(self, text: str, *, user_text: str = "", expected_language: str = "tr") -> ResponseQualityResult:
        normalized = unicodedata.normalize("NFC", str(text or "")).replace("\x00", "")
        normalized = _ROLE_PREFIX.sub("", normalized.strip())
        normalized = re.sub(r"[ \t]+", " ", normalized)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized).strip()
        words = re.findall(r"[^\W\d_]+(?:['’-][^\W\d_]+)?", normalized.casefold(), re.UNICODE)
        user_words = frozenset(
            re.findall(r"[^\W\d_]+(?:['’-][^\W\d_]+)?", user_text.casefold(), re.UNICODE)
        )
        sentences = _sentences(normalized)
        repetition = _repetition_score(sentences, words)
        mixing = _language_mixing_score(words, user_words) if expected_language == "tr" else 0.0
        malformed_hits = len(_MALFORMED.findall(normalized))
        foreign_phrase = bool(_FOREIGN_PHRASE.search(normalized))
        foreign_word_count = sum(word in _COMMON_FOREIGN for word in words)
        english_leak_count = sum(
            word in _COMMON_ENGLISH
            for word in words
            if word not in _ALLOWED_TECHNICAL and word not in user_words
        )
        foreign_word_leak = expected_language == "tr" and (foreign_word_count > 0 or english_leak_count >= 2)
        persona = bool(_BAD_PERSONA.search(normalized))
        substantive_user = _is_substantive_user(user_text)
        irrelevant_greeting = bool(substantive_user and _GREETING.search(normalized) and not _GREETING.search(user_text.strip()))
        generic_boilerplate = bool(
            substantive_user
            and (_GENERIC_HELP.search(normalized) or (len(sentences) >= 4 and _GENERIC_CLOSING.search(normalized)))
        )
        meta_leak = bool(_META_LEAK.search(normalized))
        punctuation_only = not any(character.isalnum() for character in normalized)
        incomplete = bool(normalized and len(words) > 5 and normalized.endswith(("…", "...", ",", ";", ":", "-")))
        malformed = min(1.0, malformed_hits * 0.45 + persona * 0.7 + irrelevant_greeting * 0.35 + incomplete * 0.35 + foreign_phrase * 0.7)
        reasons = []
        if not normalized or punctuation_only:
            reasons.append("empty_or_punctuation")
        if repetition >= 0.42:
            reasons.append("repetition")
        if mixing >= 0.28:
            reasons.append("language_mixing")
        if foreign_phrase:
            reasons.append("foreign_phrase")
        if foreign_word_leak:
            reasons.append("foreign_word_leak")
        if irrelevant_greeting or generic_boilerplate:
            reasons.append("generic_boilerplate")
        if meta_leak:
            reasons.append("meta_leak")
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
                "foreign_phrase_detected": foreign_phrase,
                "foreign_word_leak_detected": foreign_word_leak,
                "generic_boilerplate_detected": irrelevant_greeting or generic_boilerplate,
                "meta_leak_detected": meta_leak,
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


def _language_mixing_score(words: list[str], user_words: frozenset[str] = frozenset()) -> float:
    if not words:
        return 0.0
    foreign = sum(
        word in _COMMON_ENGLISH or word in _COMMON_FOREIGN or _looks_mixed(word)
        for word in words
        if word not in _ALLOWED_TECHNICAL and word not in user_words
    )
    return foreign / max(1, len(words))


def _looks_mixed(word: str) -> bool:
    return bool(re.search(r"(?:images?|things?|about|today|progress|response|task|file|chat)(?:'?(?:ı|i|u|ü|lar|ler|da|de|dan|den))?$", word))


def _is_substantive_user(text: str) -> bool:
    normalized = " ".join(text.casefold().split())
    if not normalized or _GREETING.fullmatch(f"{normalized} "):
        return False
    return normalized.endswith("?") or len(re.findall(r"[^\W\d_]+", normalized, re.UNICODE)) >= 3
