"""Typed models used by safe task templates."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import date, datetime, time
from enum import Enum
import re
from types import MappingProxyType
from typing import Any

from lina.agent.models import AgentPlan


_TEMPLATE_ID = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
PlanFactory = Callable[[Mapping[str, Any]], AgentPlan]


class TaskTemplateCategory(str, Enum):
    REMINDERS = "reminders"
    SCHEDULE = "schedule"
    MEMORY = "memory"
    CONVERSATION = "conversation"
    FILES_READ_ONLY = "files_read_only"
    VISION = "vision"
    SYSTEM_STATUS = "system_status"
    ORGANIZATION = "organization"
    CUSTOM = "custom"


@dataclass(frozen=True, slots=True)
class TaskTemplate:
    template_id: str
    title: str
    description: str
    category: TaskTemplateCategory
    example_phrases: tuple[str, ...]
    required_capabilities: frozenset[str]
    optional_capabilities: frozenset[str]
    input_schema: Mapping[str, type | tuple[type, ...]]
    plan_factory: PlanFactory = field(compare=False, repr=False)
    risk_summary: str = "Salt okunur"
    supported_modes: frozenset[str] = frozenset({"agent"})
    version: int = 1
    enabled: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "category", TaskTemplateCategory(self.category))
        object.__setattr__(self, "example_phrases", tuple(self.example_phrases))
        object.__setattr__(self, "required_capabilities", frozenset(self.required_capabilities))
        object.__setattr__(self, "optional_capabilities", frozenset(self.optional_capabilities))
        object.__setattr__(self, "supported_modes", frozenset(self.supported_modes))
        schema = dict(self.input_schema)
        object.__setattr__(self, "input_schema", MappingProxyType(schema))
        if not _TEMPLATE_ID.fullmatch(self.template_id):
            raise ValueError("Geçersiz görev şablonu kimliği.")
        if not self.title.strip() or not self.description.strip() or not self.example_phrases:
            raise ValueError("Görev şablonu başlık, açıklama ve örnek içermeli.")
        if not callable(self.plan_factory):
            raise TypeError("Görev şablonu plan_factory sağlamalı.")
        if self.required_capabilities & self.optional_capabilities:
            raise ValueError("Bir capability hem zorunlu hem opsiyonel olamaz.")
        if not all(_valid_schema_type(kind) for kind in schema.values()):
            raise TypeError("Görev şablonu input schema türleri geçersiz.")
        if self.version < 1:
            raise ValueError("Görev şablonu sürümü pozitif olmalı.")

    def supports(self, available_capabilities: set[str] | frozenset[str]) -> bool:
        return self.enabled and self.required_capabilities.issubset(available_capabilities)

    def create_plan(self, parameters: Mapping[str, Any]) -> AgentPlan:
        unknown = set(parameters) - set(self.input_schema)
        if unknown:
            raise ValueError("Şablon izin verilmeyen parametre içeriyor.")
        for name, kind in self.input_schema.items():
            if name not in parameters:
                raise ValueError(f"Şablon için '{name}' bilgisi eksik.")
            if not isinstance(parameters[name], kind):
                raise TypeError(f"'{name}' parametresi beklenen türde değil.")
        return self.plan_factory(MappingProxyType(dict(parameters)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "example_phrases": list(self.example_phrases),
            "required_capabilities": sorted(self.required_capabilities),
            "optional_capabilities": sorted(self.optional_capabilities),
            "input_schema": {name: _schema_name(kind) for name, kind in self.input_schema.items()},
            "risk_summary": self.risk_summary,
            "supported_modes": sorted(self.supported_modes),
            "version": self.version,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any], plan_factory: PlanFactory) -> "TaskTemplate":
        """Load public template metadata; schema v0 is migrated to v1."""
        version = max(1, int(raw.get("version", 1)))
        schema = raw.get("input_schema", {})
        if not isinstance(schema, Mapping):
            raise TypeError("Görev şablonu input schema geçersiz.")
        return cls(
            template_id=str(raw.get("template_id", "")),
            title=str(raw.get("title", "")),
            description=str(raw.get("description", "")),
            category=TaskTemplateCategory(str(raw.get("category", "custom"))),
            example_phrases=tuple(str(item) for item in raw.get("example_phrases", ())),
            required_capabilities=frozenset(str(item) for item in raw.get("required_capabilities", ())),
            optional_capabilities=frozenset(str(item) for item in raw.get("optional_capabilities", ())),
            input_schema={str(name): _schema_type(kind) for name, kind in schema.items()},
            plan_factory=plan_factory,
            risk_summary=str(raw.get("risk_summary", "Salt okunur")),
            supported_modes=frozenset(str(item) for item in raw.get("supported_modes", ("agent",))),
            version=version,
            enabled=bool(raw.get("enabled", True)),
        )


@dataclass(frozen=True, slots=True)
class TaskTemplateMatch:
    template_id: str | None
    confidence: float
    matched_signals: tuple[str, ...] = ()
    extracted_parameters: Mapping[str, Any] = field(default_factory=dict)
    missing_parameters: tuple[str, ...] = ()
    ambiguous: bool = False
    reason_code: str = "no_match"

    def __post_init__(self) -> None:
        object.__setattr__(self, "confidence", max(0.0, min(1.0, float(self.confidence))))
        object.__setattr__(self, "matched_signals", tuple(self.matched_signals))
        object.__setattr__(self, "missing_parameters", tuple(dict.fromkeys(self.missing_parameters)))
        object.__setattr__(self, "extracted_parameters", MappingProxyType(dict(self.extracted_parameters)))


@dataclass(frozen=True, slots=True)
class TaskTemplatePreflight:
    template_id: str
    title: str
    plan_summary: str
    required_information: tuple[str, ...]
    has_persistent_action: bool
    estimated_step_count: int
    risk_summary: str


@dataclass(frozen=True, slots=True)
class ReminderTemplateInput:
    title: str
    due_at: datetime
    recurrence: str = "none"


@dataclass(frozen=True, slots=True)
class MemoryTemplateInput:
    content: str
    category: str = "conversation_note"


@dataclass(frozen=True, slots=True)
class FileSummaryTemplateInput:
    target: str
    summary_length: str = "short"


def _valid_schema_type(kind: object) -> bool:
    return isinstance(kind, type) or (
        isinstance(kind, tuple) and bool(kind) and all(isinstance(item, type) for item in kind)
    )


def _schema_name(kind: type | tuple[type, ...]) -> str:
    if isinstance(kind, tuple):
        return " | ".join(item.__name__ for item in kind)
    return kind.__name__


_SCHEMA_TYPES = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "date": date,
    "time": time,
    "datetime": datetime,
    "dict": dict,
}


def _schema_type(value: object) -> type | tuple[type, ...]:
    names = [item.strip() for item in str(value).split("|")]
    try:
        kinds = tuple(_SCHEMA_TYPES[name] for name in names)
    except KeyError as error:
        raise TypeError("Görev şablonu bilinmeyen schema türü içeriyor.") from error
    return kinds[0] if len(kinds) == 1 else kinds
