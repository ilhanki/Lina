"""Argument parsing and validation for deterministic intents."""

import re
from datetime import datetime, timedelta, timezone

from lina.notifications.models import ReminderRecurrence


TIME_PATTERN = re.compile(r"(?:saat\s*)?(?P<hour>[01]?\d|2[0-3])(?:[.:](?P<minute>[0-5]\d))?\b", re.IGNORECASE)


def parse_reminder_arguments(text: str, now: datetime | None = None) -> tuple[dict[str, object], tuple[str, ...]]:
    current = (now or datetime.now().astimezone()).astimezone()
    normalized = " ".join(text.casefold().replace("’", "'").split())
    recurrence = ReminderRecurrence.NONE
    if "her gün" in normalized:
        recurrence = ReminderRecurrence.DAILY
    elif "her hafta" in normalized:
        recurrence = ReminderRecurrence.WEEKLY
    day_offset = 1 if "yarın" in normalized else 0 if "bugün" in normalized else None
    match = TIME_PATTERN.search(normalized)
    missing: list[str] = []
    if day_offset is None:
        missing.append("date")
    if match is None:
        missing.append("time")
    due_at = None
    if day_offset is not None and match is not None:
        local_day = (current + timedelta(days=day_offset)).date()
        due_local = datetime.combine(local_day, datetime.min.time(), tzinfo=current.tzinfo).replace(
            hour=int(match.group("hour")), minute=int(match.group("minute") or 0)
        )
        due_at = due_local.astimezone(timezone.utc)
        if due_at <= current.astimezone(timezone.utc):
            missing.append("future_time")
    title = _extract_reminder_title(text)
    if not title:
        missing.append("title")
    return {"title": title, "due_at": due_at, "recurrence": recurrence}, tuple(dict.fromkeys(missing))


def _extract_reminder_title(text: str) -> str:
    value = re.sub(r"\b(bana|beni|diye|için|hatırlatıcı|oluştur|hatırlat)\b", " ", text, flags=re.IGNORECASE)
    value = re.sub(r"\b(bugün|yarın|her gün|her hafta|saat)\b", " ", value, flags=re.IGNORECASE)
    value = re.sub(
        r"(?:saat\s*)?(?:[01]?\d|2[0-3])(?:[.:][0-5]\d)?(?:['’]?(?:da|de|ta|te))?",
        " ",
        value,
        flags=re.IGNORECASE,
    )
    return " ".join(value.strip(" .,!?:;'\"").split()).capitalize()


def extract_file_target(text: str) -> str:
    value = re.sub(r"\b(dosyasını|dosyayı|dosyasını|oku|okur musun|lütfen)\b", " ", text, flags=re.IGNORECASE)
    return " ".join(value.strip(" .,!?:;'\"").split())


def extract_memory_content(text: str) -> str:
    match = re.search(r"(?:şunu hatırla|hatırla|unutma|bunu kaydet)\s*[:：]?\s*(.*)", text, re.IGNORECASE)
    if match and match.group(1).strip():
        return match.group(1).strip()
    trailing = re.match(r"(.*?)\s+unutma[.!]?$", text, re.IGNORECASE)
    return trailing.group(1).strip() if trailing else ""
