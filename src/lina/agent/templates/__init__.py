"""Typed, framework-neutral Agent task templates."""

from lina.agent.templates.builtins import build_builtin_template_registry
from lina.agent.templates.matcher import TaskTemplateMatcher
from lina.agent.templates.models import (
    FileSummaryTemplateInput,
    MemoryTemplateInput,
    ReminderTemplateInput,
    TaskTemplate,
    TaskTemplateCategory,
    TaskTemplateMatch,
    TaskTemplatePreflight,
)
from lina.agent.templates.registry import TaskTemplateRegistry
from lina.agent.templates.renderer import render_preflight
from lina.agent.templates.validators import TemplateInputError, normalize_template_input

__all__ = [
    "FileSummaryTemplateInput",
    "MemoryTemplateInput",
    "ReminderTemplateInput",
    "TaskTemplate",
    "TaskTemplateCategory",
    "TaskTemplateMatch",
    "TaskTemplateMatcher",
    "TaskTemplatePreflight",
    "TaskTemplateRegistry",
    "TemplateInputError",
    "build_builtin_template_registry",
    "normalize_template_input",
    "render_preflight",
]
