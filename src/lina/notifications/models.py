"""Framework-neutral notification models."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ReminderRecurrence(str, Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"


class ReminderStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    DELETED = "deleted"


@dataclass(frozen=True, slots=True)
class Reminder:
    id: int | None
    title: str
    due_at: datetime
    recurrence: ReminderRecurrence = ReminderRecurrence.NONE
    status: ReminderStatus = ReminderStatus.ACTIVE
    created_at: datetime | None = None
    completed_at: datetime | None = None
    last_notified_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Reminder title must not be empty")
        if self.due_at.tzinfo is None:
            raise ValueError("Reminder due_at must be timezone-aware")

