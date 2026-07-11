"""Presentation-only formatting helpers for Lina's Qt interface."""

from __future__ import annotations

import re


_LABEL_PREFIX_PATTERN = re.compile(
    r"^\s*(?:(?:lina|assistant|asistan)\s*:\s*)+",
    flags=re.IGNORECASE,
)


def normalize_assistant_text(text: str) -> str:
    """Remove repeated assistant transcript labels from rendered responses."""
    normalized = text.strip()
    while True:
        updated = _LABEL_PREFIX_PATTERN.sub("", normalized).strip()
        if updated == normalized:
            return normalized
        normalized = updated


def format_welcome_message() -> str:
    """Return the first visible assistant message for a fresh GUI session."""
    return (
        "Merhaba İlhan. Ben Lina, yerel çalışan masaüstü asistanın.\n"
        "Hazırım."
    )


def derive_session_title(message: str, max_length: int = 44) -> str:
    """Create a compact local session title from the first meaningful user request."""
    title = " ".join(message.strip().split())
    if not title:
        return "Yeni Sohbet"
    lowered = title.casefold()
    if lowered in {"selam", "merhaba", "naber", "nasılsın", "selam naber"}:
        return "Yeni Sohbet"
    if len(title) <= max_length:
        return title
    return f"{title[: max_length - 1].rstrip()}..."


def friendly_error_message(error: Exception) -> str:
    """Map controlled runtime failures to a short Turkish GUI message."""
    name = error.__class__.__name__.casefold()
    message = str(error).strip()
    if "timeout" in name or "timeout" in message.casefold():
        return (
            "Model yanıt vermedi İlhan. Ollama çalışıyor olabilir ama bu istek "
            "zaman aşımına uğradı."
        )
    if "provider" in name or "ollama" in message.casefold():
        return (
            "Modele ulaşılamadı İlhan. Ollama'nın çalıştığını ve modelin yüklü "
            "olduğunu kontrol edebilirsin."
        )
    return "Bir şey ters gitti İlhan. İstersen tekrar deneyebiliriz."
