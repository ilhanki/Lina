"""SQLite persistence for local reminders."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from collections.abc import Iterator

from lina.notifications.models import Reminder, ReminderRecurrence, ReminderStatus


class NotificationRepository:
    """Persist reminders with one short-lived SQLite connection per operation."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path.resolve(strict=False)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                due_at TEXT NOT NULL,
                recurrence TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                last_notified_at TEXT
            )""")

    def create(self, reminder: Reminder) -> Reminder:
        now = _utc(reminder.created_at or datetime.now(timezone.utc))
        with self._connection() as connection:
            cursor = connection.execute(
                "INSERT INTO reminders(title, due_at, recurrence, status, created_at) VALUES (?, ?, ?, ?, ?)",
                (reminder.title.strip(), _serialize(reminder.due_at), reminder.recurrence.value, reminder.status.value, _serialize(now)),
            )
        return Reminder(reminder.id or int(cursor.lastrowid), reminder.title.strip(), _utc(reminder.due_at), reminder.recurrence, reminder.status, now)

    def list(self, include_deleted: bool = False) -> tuple[Reminder, ...]:
        query = "SELECT * FROM reminders"
        if not include_deleted:
            query += " WHERE status != 'deleted'"
        query += " ORDER BY due_at ASC, id ASC"
        with self._connection() as connection:
            return tuple(_row(row) for row in connection.execute(query))

    def update(self, reminder: Reminder) -> Reminder:
        if reminder.id is None:
            raise ValueError("Reminder id is required")
        with self._connection() as connection:
            connection.execute(
                "UPDATE reminders SET title=?, due_at=?, recurrence=?, status=?, completed_at=?, last_notified_at=? WHERE id=?",
                (reminder.title.strip(), _serialize(reminder.due_at), reminder.recurrence.value, reminder.status.value, _optional(reminder.completed_at), _optional(reminder.last_notified_at), reminder.id),
            )
        return reminder

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()


def _utc(value: datetime) -> datetime:
    return value.astimezone(timezone.utc)


def _serialize(value: datetime) -> str:
    return _utc(value).isoformat()


def _optional(value: datetime | None) -> str | None:
    return _serialize(value) if value else None


def _row(row: sqlite3.Row) -> Reminder:
    return Reminder(int(row["id"]), row["title"], datetime.fromisoformat(row["due_at"]), ReminderRecurrence(row["recurrence"]), ReminderStatus(row["status"]), datetime.fromisoformat(row["created_at"]), datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None, datetime.fromisoformat(row["last_notified_at"]) if row["last_notified_at"] else None)
