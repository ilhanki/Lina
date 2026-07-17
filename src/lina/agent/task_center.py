"""Typed Task Center projections over privacy-safe Agent metadata."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from lina.agent.persistence import AgentSessionRepository


class TaskCenterSection(str, Enum):
    ACTIVE = "active"
    WAITING_APPROVAL = "waiting_approval"
    PAUSED = "paused"
    INTERRUPTED = "interrupted"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class AgentTaskSummary:
    session_id: str
    title: str
    template_id: str | None
    status: str
    started_at: datetime | None
    progress_current: int
    progress_total: int
    conversation_id: int | None
    last_summary: str
    section: TaskCenterSection
    actions: tuple[str, ...]
    error_code: str | None = None

    @property
    def progress_percent(self) -> int:
        if self.progress_total <= 0:
            return 0
        return min(100, round(self.progress_current / self.progress_total * 100))


@dataclass(frozen=True, slots=True)
class RecoveryNotice:
    count: int
    message: str
    actions: tuple[str, ...] = ("İncele", "Güvenli Kopya", "Geçmişte Bırak")


class AgentTaskCenter:
    def __init__(self, repository: AgentSessionRepository) -> None:
        self.repository = repository

    def list(self, section: TaskCenterSection | str | None = None) -> tuple[AgentTaskSummary, ...]:
        resolved = TaskCenterSection(section) if section is not None else None
        summaries = tuple(_summary(item) for item in self.repository.load_all())
        if resolved is not None:
            summaries = tuple(item for item in summaries if item.section is resolved)
        return tuple(sorted(summaries, key=lambda item: _sort_value(item.started_at), reverse=True))

    def sections(self) -> dict[TaskCenterSection, tuple[AgentTaskSummary, ...]]:
        items = self.list()
        return {section: tuple(item for item in items if item.section is section) for section in TaskCenterSection}

    def get(self, session_id: str) -> AgentTaskSummary | None:
        return next((item for item in self.list() if item.session_id == session_id), None)

    def remove_history(self, session_id: str) -> bool:
        return self.repository.remove(session_id)

    def recovery_notice(self) -> RecoveryNotice | None:
        count = len(self.list(TaskCenterSection.INTERRUPTED))
        if not count:
            return None
        message = "Yarım kalan bir Agent görevin var." if count == 1 else f"Yarım kalan {count} Agent görevin var."
        return RecoveryNotice(count, message)

    def cleanup(self, retention_days: int | None) -> int:
        return self.repository.cleanup(retention_days)


def _summary(raw: dict[str, Any]) -> AgentTaskSummary:
    status = str(raw.get("status", "failed"))
    plan = raw.get("plan") if isinstance(raw.get("plan"), dict) else {}
    steps = plan.get("steps") if isinstance(plan.get("steps"), list) else []
    completed = sum(item.get("status") in {"succeeded", "skipped"} for item in steps if isinstance(item, dict))
    total = len(steps)
    section = _section(status)
    return AgentTaskSummary(
        session_id=str(raw.get("session_id", "")),
        title=str(raw.get("title") or "Agent görevi")[:120],
        template_id=str(raw["template_id"]) if raw.get("template_id") else None,
        status=status,
        started_at=_parse_datetime(raw.get("created_at")),
        progress_current=min(completed, total),
        progress_total=total,
        conversation_id=raw.get("conversation_id") if isinstance(raw.get("conversation_id"), int) else None,
        last_summary=str(raw.get("last_summary") or "Agent görevi güncellendi.")[:160],
        section=section,
        actions=_actions(section),
        error_code=str(raw["error_code"]) if raw.get("error_code") else None,
    )


def _section(status: str) -> TaskCenterSection:
    if status in {"idle", "planning", "awaiting_input", "ready", "running", "replanning"}:
        return TaskCenterSection.ACTIVE
    if status in {"awaiting_plan_approval", "awaiting_step_approval"}:
        return TaskCenterSection.WAITING_APPROVAL
    if status == "paused":
        return TaskCenterSection.PAUSED
    if status == "interrupted":
        return TaskCenterSection.INTERRUPTED
    if status in {"completed", "partially_completed"}:
        return TaskCenterSection.COMPLETED
    if status == "cancelled":
        return TaskCenterSection.CANCELLED
    return TaskCenterSection.FAILED


def _actions(section: TaskCenterSection) -> tuple[str, ...]:
    if section in {TaskCenterSection.ACTIVE, TaskCenterSection.WAITING_APPROVAL, TaskCenterSection.PAUSED}:
        return ("Aç",)
    if section is TaskCenterSection.INTERRUPTED:
        return ("İncele", "Güvenli kopya olarak yeniden başlat", "Geçmişte bırak")
    if section in {TaskCenterSection.FAILED, TaskCenterSection.CANCELLED}:
        return ("Sonucu görüntüle", "Güvenli kopya olarak yeniden başlat", "Geçmişten kaldır")
    return ("Sonucu görüntüle", "Geçmişten kaldır")


def _parse_datetime(value: object) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _sort_value(value: datetime | None) -> float:
    if value is None:
        return 0.0
    try:
        return value.timestamp()
    except (OSError, OverflowError, ValueError):
        return 0.0
