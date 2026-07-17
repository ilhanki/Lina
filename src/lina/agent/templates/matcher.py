"""Conservative deterministic matching for safe task templates."""

from __future__ import annotations

import re

from lina.agent.templates.models import TaskTemplateMatch
from lina.agent.templates.registry import TaskTemplateRegistry
from lina.agent.templates.validators import normalize_template_input


class TaskTemplateMatcher:
    def __init__(self, registry: TaskTemplateRegistry) -> None:
        self.registry = registry

    def match(
        self,
        text: str,
        *,
        available_capabilities: set[str] | frozenset[str],
        agent_mode_enabled: bool = True,
        explicit_template_id: str | None = None,
    ) -> TaskTemplateMatch:
        if not agent_mode_enabled:
            return TaskTemplateMatch(None, 0.0, reason_code="agent_mode_disabled")
        if explicit_template_id:
            template = self.registry.get(explicit_template_id)
            if template is None or not template.supports(available_capabilities):
                return TaskTemplateMatch(None, 0.0, reason_code="template_unavailable")
            parameters, missing = normalize_template_input(template.template_id, text)
            return TaskTemplateMatch(template.template_id, 1.0, ("explicit_selection",), parameters, missing, False, "explicit_selection")

        normalized = _normalize(text)
        if not normalized or _is_explanation(normalized):
            return TaskTemplateMatch(None, 0.0, reason_code="normal_chat")
        candidates: list[tuple[str, float, tuple[str, ...]]] = []
        reminder_action = bool(re.search(r"\b(hatırlat|hatirlat|hatırlatıcı oluştur|hatirlatici olustur)\b", normalized))
        if reminder_action:
            candidates.append(("reminders.create", 0.96, ("reminder_action",)))
        if _contains_any(normalized, ("hatırlatıcılarımı özetle", "hatirlaticilarimi ozetle", "hatırlatıcıları listele", "hatirlaticilari listele")):
            candidates.append(("reminders.summary", 0.98, ("reminder_entity", "summary_action")))
        if "hatırlat" in normalized and _contains_any(normalized, ("çakış", "cakış", "cakisim", "çakışıyor")):
            candidates.append(("reminders.conflicts", 0.98, ("reminder_entity", "conflict_action")))
        if _contains_any(normalized, ("bunu hatırla", "bunu hatirla", "şunu hatırla", "sunu hatirla", "bunu kaydet", "unutma")) or re.search(r"\b(hatırla|hatirla)\b", normalized):
            candidates.append(("memory.store", 0.95, ("memory_action",)))
        if _contains_any(normalized, ("neleri hatırlıyorsun", "neleri hatirliyorsun", "ne hatırlıyorsun", "hafızanda", "hafizanda")):
            candidates.append(("memory.recall", 0.97, ("memory_query",)))
        if _contains_any(normalized, ("dosyasını oku", "dosyasini oku", "dosyayı oku", "dosyayi oku")) and _contains_any(normalized, ("özet", "ozet")):
            candidates.append(("files.summarize", 0.96, ("file_entity", "read_only_action")))
        if _contains_any(normalized, ("ekran görüntüsünde", "ekran goruntusunde", "görselde", "gorselde")) and _contains_any(normalized, ("analiz", "önemli", "onemli", "söyle", "soyle")):
            candidates.append(("vision.single_frame", 0.94, ("single_frame", "vision_action")))

        supported = [item for item in candidates if (self.registry.get(item[0]) and self.registry.require(item[0]).supports(available_capabilities))]
        if not supported:
            return TaskTemplateMatch(None, 0.0, reason_code="no_match")
        supported.sort(key=lambda item: (-item[1], item[0]))
        best = supported[0]
        ambiguous = len(supported) > 1 and supported[1][1] >= best[1] - 0.03
        if ambiguous:
            return TaskTemplateMatch(None, best[1], best[2] + supported[1][2], ambiguous=True, reason_code="ambiguous_match")
        parameters, missing = normalize_template_input(best[0], text)
        return TaskTemplateMatch(best[0], best[1], best[2], parameters, missing, False, "matched")


def _normalize(text: str) -> str:
    return " ".join(text.casefold().replace("’", "'").split()).strip(" .!?\n\t")


def _contains_any(text: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in text for phrase in phrases)


def _is_explanation(text: str) -> bool:
    subjects = ("hatırlatıcı", "hatirlatici", "memory", "hafıza", "hafiza", "görev şablonu", "gorev sablonu", "retry", "agent")
    questions = ("nedir", "nasıl çalış", "nasil calis", "neden", "ne demek", "güvenli mi", "guvenli mi")
    return any(subject in text for subject in subjects) and any(question in text for question in questions)
