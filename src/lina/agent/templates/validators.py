"""Schema validation and conservative parameter normalization."""

from __future__ import annotations

from datetime import datetime
import re
from typing import Any

from lina.brain.routing.validation import extract_file_target, extract_memory_content, parse_reminder_arguments


class TemplateInputError(ValueError):
    def __init__(self, message: str, missing: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.missing = missing


def normalize_template_input(
    template_id: str,
    text: str,
    *,
    now: datetime | None = None,
) -> tuple[dict[str, Any], tuple[str, ...]]:
    if template_id == "reminders.create":
        arguments, missing = parse_reminder_arguments(text, now)
        parameters = {
            "title": str(arguments.get("title") or "").strip(),
            "due_at": arguments.get("due_at"),
            "recurrence": getattr(arguments.get("recurrence"), "value", arguments.get("recurrence", "none")),
        }
        return parameters, tuple(missing)
    if template_id in {"reminders.summary", "reminders.conflicts"}:
        normalized = _normalize(text)
        range_name = "week" if "hafta" in normalized else "tomorrow" if "yarın" in normalized else "upcoming"
        return {"range": range_name}, ()
    if template_id == "memory.store":
        content = extract_memory_content(text)
        if not content:
            trailing = re.match(r"(.*?)\s+(?:hatırla|hatirla)[.!]?$", text, re.IGNORECASE)
            content = trailing.group(1).strip() if trailing else ""
        if not content and _normalize(text) in {"bunu hatırla", "bunu hatirla", "hatırla", "hatirla"}:
            return {"content": "", "category": "conversation_note"}, ("content",)
        return {"content": content, "category": "conversation_note"}, (() if content else ("content",))
    if template_id == "memory.recall":
        return {"query": text.strip()[:240]}, ()
    if template_id == "files.summarize":
        target = _quoted_path(text) or extract_file_target(text)
        if _normalize(target) in {"bu metin ve özetle", "bu metin ve ozetle", "bu dosya ve özetle", "bu dosya ve ozetle"}:
            target = ""
        return {"target": target, "summary_length": "short"}, (() if target else ("target",))
    if template_id == "vision.single_frame":
        return {}, ()
    return {}, ()


def validate_parameters(schema: dict[str, type | tuple[type, ...]], parameters: dict[str, Any]) -> None:
    unknown = set(parameters) - set(schema)
    if unknown:
        raise TemplateInputError("Şablon izin verilmeyen parametre içeriyor.")
    missing = tuple(name for name in schema if name not in parameters or parameters[name] in {None, ""})
    if missing:
        raise TemplateInputError("Görevi başlatmak için bazı bilgiler eksik.", missing)
    for name, kind in schema.items():
        value = parameters[name]
        if not isinstance(value, kind):
            raise TemplateInputError(f"'{name}' bilgisi beklenen türde değil.")
        if isinstance(value, str) and not value.strip():
            raise TemplateInputError(f"'{name}' bilgisi boş olamaz.", (name,))
        if name == "due_at" and isinstance(value, datetime):
            if value.tzinfo is None or value.utcoffset() is None:
                raise TemplateInputError("Hatırlatma zamanı saat dilimi içermeli.")
            if value <= datetime.now(value.tzinfo):
                raise TemplateInputError("Hatırlatma zamanı gelecekte olmalı.")
        if name == "recurrence" and getattr(value, "value", value) not in {"none", "daily", "weekly"}:
            raise TemplateInputError("Tekrarlama seçeneği geçersiz.")
        if name == "range" and value not in {"upcoming", "tomorrow", "week"}:
            raise TemplateInputError("Tarih aralığı geçersiz.")
        if name == "summary_length" and value not in {"short", "medium"}:
            raise TemplateInputError("Özet uzunluğu geçersiz.")


def _normalize(text: str) -> str:
    return " ".join(text.casefold().replace("’", "'").split()).strip(" .!?\n\t")


def _quoted_path(text: str) -> str:
    match = re.search(r"[\"“”']([^\"“”']+\.(?:txt|md|json|csv|log))[\"“”']", text, re.IGNORECASE)
    return match.group(1).strip() if match else ""
