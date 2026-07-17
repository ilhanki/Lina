"""Deterministic registry for enabled and available task templates."""

from __future__ import annotations

from lina.agent.templates.models import TaskTemplate, TaskTemplateCategory


class TaskTemplateRegistry:
    def __init__(self) -> None:
        self._templates: dict[str, TaskTemplate] = {}

    def register(self, template: TaskTemplate) -> None:
        if template.template_id in self._templates:
            raise ValueError(f"Görev şablonu zaten kayıtlı: {template.template_id}")
        self._templates[template.template_id] = template

    def get(self, template_id: str) -> TaskTemplate | None:
        return self._templates.get(template_id)

    def require(self, template_id: str) -> TaskTemplate:
        template = self.get(template_id)
        if template is None:
            raise KeyError(f"Bilinmeyen görev şablonu: {template_id}")
        return template

    def list(
        self,
        *,
        category: TaskTemplateCategory | str | None = None,
        enabled_only: bool = True,
        available_capabilities: set[str] | frozenset[str] | None = None,
    ) -> tuple[TaskTemplate, ...]:
        selected = tuple(self._templates.values())
        if category is not None:
            resolved = TaskTemplateCategory(category)
            selected = tuple(item for item in selected if item.category is resolved)
        if enabled_only:
            selected = tuple(item for item in selected if item.enabled)
        if available_capabilities is not None:
            selected = tuple(item for item in selected if item.supports(available_capabilities))
        return tuple(sorted(selected, key=lambda item: (item.category.value, item.title.casefold(), item.template_id)))

    def ids(self) -> tuple[str, ...]:
        return tuple(item.template_id for item in self.list(enabled_only=False))
