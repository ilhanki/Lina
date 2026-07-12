"""Application service for local reminders."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from lina.notifications.models import Reminder, ReminderRecurrence, ReminderStatus
from lina.notifications.repository import NotificationRepository


class NotificationService:
    """Validate and coordinate reminder operations."""

    def __init__(self, repository: NotificationRepository) -> None:
        self._repository = repository

    def create(self, title: str, due_at: datetime, recurrence: ReminderRecurrence | str = ReminderRecurrence.NONE) -> Reminder:
        due_at = _utc(due_at)
        if due_at <= datetime.now(timezone.utc):
            raise ValueError("Hatırlatma zamanı gelecekte olmalı.")
        try:
            recurrence = ReminderRecurrence(recurrence)
        except (TypeError, ValueError) as exc:
            raise ValueError("Geçersiz tekrarlama seçeneği.") from exc
        try:
            return self._repository.create(Reminder(None, title, due_at, recurrence))
        except ValueError:
            raise
        except Exception as exc:
            raise RuntimeError("Hatırlatıcı kaydedilemedi.") from exc

    def list(self) -> tuple[Reminder, ...]:
        return self._repository.list()

    def update(self, reminder: Reminder) -> Reminder:
        try:
            return self._repository.update(reminder)
        except ValueError:
            raise
        except Exception as exc:
            raise RuntimeError("Hatırlatıcı güncellenemedi.") from exc

    def events(self):
        return self._repository.list_events()

    def unread_count(self) -> int:
        return self._repository.unread_event_count()

    def mark_read(self, event_id: int) -> None:
        self._repository.mark_event_read(event_id)

    def mark_all_read(self) -> None:
        self._repository.mark_all_events_read()

    def complete(self, reminder: Reminder) -> Reminder:
        return self.update(Reminder(reminder.id, reminder.title, reminder.due_at, reminder.recurrence, ReminderStatus.COMPLETED, reminder.created_at, _utc(datetime.now(timezone.utc))))

    def delete(self, reminder: Reminder) -> Reminder:
        return self.update(Reminder(reminder.id, reminder.title, reminder.due_at, reminder.recurrence, ReminderStatus.DELETED, reminder.created_at, reminder.completed_at, reminder.last_notified_at))

    def snooze(self, reminder: Reminder, duration: timedelta) -> Reminder:
        if duration not in (timedelta(minutes=10), timedelta(hours=1)):
            raise ValueError("Unsupported snooze duration")
        return self.update(Reminder(reminder.id, reminder.title, _utc(reminder.due_at + duration), reminder.recurrence, ReminderStatus.ACTIVE, reminder.created_at))

    def snooze_tomorrow(self, reminder: Reminder) -> Reminder:
        return self.update(Reminder(reminder.id, reminder.title, _utc(reminder.due_at + timedelta(days=1)), reminder.recurrence, ReminderStatus.ACTIVE, reminder.created_at))


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("Reminder time must be timezone-aware")
    return value.astimezone(timezone.utc)


def next_occurrence(reminder: Reminder) -> datetime | None:
    if reminder.recurrence is ReminderRecurrence.NONE:
        return None
    days = 1 if reminder.recurrence is ReminderRecurrence.DAILY else 7
    return reminder.due_at + timedelta(days=days)
