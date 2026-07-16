"""Dependency-free, in-memory PCM and transcription normalization."""

from __future__ import annotations

from array import array
import re
import unicodedata


def preprocess_pcm16(pcm_data: bytes, *, target_peak: float = 0.72, max_gain: float = 3.0) -> bytes:
    """Correct DC offset and apply bounded gain without clipping."""
    if not pcm_data or len(pcm_data) % 2:
        return pcm_data
    samples = array("h")
    samples.frombytes(pcm_data)
    if not samples:
        return pcm_data
    mean = sum(samples) / len(samples)
    centered = [sample - mean for sample in samples]
    peak = max((abs(value) for value in centered), default=0.0)
    if peak < 1.0:
        return array("h", [0] * len(samples)).tobytes()
    gain = min(max_gain, target_peak * 32767.0 / peak)
    processed = array("h", (round(max(-32767, min(32767, value * gain))) for value in centered))
    return processed.tobytes()


_EMPTY_MARKERS = re.compile(r"(?i)^\s*(?:\[blank_audio\]|\[silence\]|\(silence\)|<\|nospeech\|>|\.{1,3})\s*$")
_NOISE_EDGE = re.compile(r"(?i)^(?:\[noise\]|\[music\]|\[applause\]|\(gürültü\))\s*|\s*(?:\[noise\]|\[music\]|\[applause\]|\(gürültü\))$")


def normalize_transcription(text: str) -> str:
    value = unicodedata.normalize("NFC", str(text or "")).replace("\x00", "").strip()
    if _EMPTY_MARKERS.fullmatch(value):
        return ""
    value = _NOISE_EDGE.sub("", value).strip()
    value = " ".join(value.split())
    if normalize_wake_text(value) in {"hey lina", "he lina"}:
        return "Hey Lina"
    return value


def normalize_wake_text(text: str) -> str:
    value = unicodedata.normalize("NFKC", text).casefold()
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    return " ".join(value.split())


def transcription_is_low_quality(text: str, confidence: float | None) -> bool:
    if confidence is not None and confidence < 0.45:
        return True
    words = re.findall(r"\w+", text, re.UNICODE)
    return not text or (len(words) == 1 and len(words[0]) < 2)
