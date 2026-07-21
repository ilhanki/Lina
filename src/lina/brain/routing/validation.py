"""Argument parsing and validation for deterministic intents."""

import re
from datetime import datetime, timedelta, timezone

from lina.notifications.models import ReminderRecurrence


TIME_PATTERN = re.compile(r"(?:saat\s*)?(?P<hour>[01]?\d|2[0-3])(?:[.:](?P<minute>[0-5]\d))?\b", re.IGNORECASE)
WEEKDAYS = {
    "pazartesi": 0,
    "salı": 1,
    "sali": 1,
    "çarşamba": 2,
    "carsamba": 2,
    "perşembe": 3,
    "persembe": 3,
    "cuma": 4,
    "cumartesi": 5,
    "pazar": 6,
}
DAYPARTS = ("sabah", "akşam", "aksam")


def parse_reminder_arguments(text: str, now: datetime | None = None) -> tuple[dict[str, object], tuple[str, ...]]:
    current = (now or datetime.now().astimezone()).astimezone()
    normalized = " ".join(text.casefold().replace("’", "'").split())
    recurrence = ReminderRecurrence.NONE
    if "her gün" in normalized:
        recurrence = ReminderRecurrence.DAILY
    elif "her hafta" in normalized or any(
        f"her {weekday}" in normalized for weekday in WEEKDAYS
    ):
        recurrence = ReminderRecurrence.WEEKLY

    target_date = None
    weekday_target = next(
        (value for name, value in WEEKDAYS.items() if re.search(rf"\b{name}\b", normalized)),
        None,
    )
    if "yarın" in normalized or "yarin" in normalized:
        target_date = (current + timedelta(days=1)).date()
    elif "bugün" in normalized or "bugun" in normalized:
        target_date = current.date()
    elif weekday_target is not None:
        days_ahead = (weekday_target - current.weekday()) % 7
        target_date = (current + timedelta(days=days_ahead)).date()

    daypart = next((item for item in DAYPARTS if re.search(rf"\b{item}\b", normalized)), None)
    match = TIME_PATTERN.search(normalized)
    missing: list[str] = []
    if match is None:
        missing.append("time")
    elif target_date is None and (daypart is not None or recurrence is ReminderRecurrence.DAILY):
        target_date = current.date()
    if target_date is None:
        missing.append("date")

    due_at = None
    if target_date is not None and match is not None:
        hour = int(match.group("hour"))
        if daypart in {"akşam", "aksam"} and hour < 12:
            hour += 12
        elif daypart == "sabah" and hour == 12:
            hour = 0
        due_local = datetime.combine(target_date, datetime.min.time(), tzinfo=current.tzinfo).replace(
            hour=hour,
            minute=int(match.group("minute") or 0),
        )
        inferred_next_occurrence = (
            weekday_target is not None
            or daypart is not None
            or recurrence is ReminderRecurrence.DAILY
        ) and "bugün" not in normalized and "bugun" not in normalized
        if due_local <= current and inferred_next_occurrence:
            interval = 7 if weekday_target is not None else 1
            due_local += timedelta(days=interval)
        due_at = due_local.astimezone(timezone.utc)
        if due_at <= current.astimezone(timezone.utc):
            missing.append("future_time")
    title = _extract_reminder_title(text)
    if not title:
        missing.append("title")
    return {"title": title, "due_at": due_at, "recurrence": recurrence}, tuple(dict.fromkeys(missing))


def _extract_reminder_title(text: str) -> str:
    value = re.sub(
        r"\b(bana|beni|diye|için|hatırlatıcı|hatirlatici|oluştur|olustur|"
        r"hatırlatır|hatirlatir|hatırlat|hatirlat|mısın|misin|musun|müsün|lütfen)\b",
        " ",
        text,
        flags=re.IGNORECASE,
    )
    value = re.sub(
        r"\b(bugün|bugun|yarın|yarin|her gün|her gun|her hafta|saat|sabah|akşam|aksam|"
        r"pazartesi|salı|sali|çarşamba|carsamba|perşembe|persembe|cuma|cumartesi|pazar)\b",
        " ",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(
        r"(?:saat\s*)?(?:[01]?\d|2[0-3])(?:[.:][0-5]\d)?(?:['’]?(?:da|de|ta|te))?",
        " ",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(r"\bvar\b", " ", value, flags=re.IGNORECASE)
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
