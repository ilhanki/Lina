"""Presentation-only formatting helpers for Lina's Qt interface."""

from __future__ import annotations

import re
from datetime import datetime, timezone


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


_TURKISH_MONTHS = (
    "Oca",
    "Şub",
    "Mar",
    "Nis",
    "May",
    "Haz",
    "Tem",
    "Ağu",
    "Eyl",
    "Eki",
    "Kas",
    "Ara",
)


def _to_local_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone()


def format_message_time(value: datetime) -> str:
    """Format a persisted timestamp as the user's local clock time."""
    return _to_local_datetime(value).strftime("%H:%M")


def format_conversation_datetime(
    value: datetime,
    now: datetime | None = None,
) -> str:
    """Format conversation activity with deterministic Turkish date labels."""
    local_value = _to_local_datetime(value)
    local_now = _to_local_datetime(now or datetime.now().astimezone())
    value_date = local_value.date()
    now_date = local_now.date()
    if value_date == now_date:
        prefix = "Bugün"
    elif (now_date - value_date).days == 1:
        prefix = "Dün"
    elif local_value.year == local_now.year:
        prefix = f"{local_value.day} {_TURKISH_MONTHS[local_value.month - 1]}"
    else:
        return f"{local_value.day} {_TURKISH_MONTHS[local_value.month - 1]} {local_value.year}"
    return f"{prefix} · {local_value:%H:%M}"


def build_welcome_message(
    now: datetime | None = None,
    conversation_id: int | None = None,
) -> tuple[str, str]:
    """Return a deterministic time-aware welcome heading and supporting line."""
    hour = (now or datetime.now().astimezone()).astimezone().hour
    if 5 <= hour < 12:
        greeting = "Günaydın İlhan."
    elif 12 <= hour < 18:
        greeting = "İyi günler İlhan."
    elif 18 <= hour < 23:
        greeting = "İyi akşamlar İlhan."
    else:
        greeting = "Gece vardiyasındayız İlhan."
    options = (
        "Bugün ne yapıyoruz?",
        "Nereden devam edelim?",
        "Sana nasıl yardımcı olayım?",
        "Lina için sıradaki adımımız ne?",
        "Bir şeyler üretmeye hazır mısın?",
    )
    day_number = (now or datetime.now().astimezone()).astimezone().timetuple().tm_yday
    index = (day_number + (conversation_id or 0)) % len(options)
    return greeting, options[index]


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
