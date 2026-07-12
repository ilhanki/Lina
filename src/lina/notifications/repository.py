"""SQLite persistence for local reminders."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from collections.abc import Iterator

from lina.notifications.models import NotificationEvent, Reminder, ReminderRecurrence, ReminderStatus


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
            connection.execute("""CREATE TABLE IF NOT EXISTS notification_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reminder_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                triggered_at TEXT NOT NULL,
                read_at TEXT,
                delivery_status TEXT NOT NULL,
                UNIQUE(reminder_id, triggered_at),
                FOREIGN KEY(reminder_id) REFERENCES reminders(id) ON DELETE CASCADE
            )""")

    def create_event(self, reminder: Reminder, triggered_at: datetime) -> NotificationEvent | None:
        with self._connection() as connection:
            cursor = connection.execute(
                "INSERT OR IGNORE INTO notification_events(reminder_id,title,triggered_at,delivery_status) VALUES(?,?,?,?)",
                (reminder.id, reminder.title, _serialize(triggered_at), "pending"),
            )
        if cursor.rowcount == 0:
            return None
        return NotificationEvent(int(cursor.lastrowid), reminder.id or 0, reminder.title, _utc(triggered_at))

    def list_events(self) -> tuple[NotificationEvent, ...]:
        with self._connection() as connection:
            rows = connection.execute("SELECT * FROM notification_events ORDER BY triggered_at DESC, id DESC")
            return tuple(_event_row(row) for row in rows)

    def unread_event_count(self) -> int:
        with self._connection() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM notification_events WHERE read_at IS NULL").fetchone()[0])

    def mark_event_read(self, event_id: int) -> None:
        with self._connection() as connection:
            connection.execute("UPDATE notification_events SET read_at=? WHERE id=?", (_serialize(datetime.now(timezone.utc)), event_id))

    def mark_all_events_read(self) -> None:
        with self._connection() as connection:
            connection.execute("UPDATE notification_events SET read_at=? WHERE read_at IS NULL", (_serialize(datetime.now(timezone.utc)),))

    def update_delivery_status(self, event_id: int, status: str) -> None:
        if status not in {"pending", "delivered", "in_app", "suppressed", "failed"}:
            raise ValueError("Invalid delivery status")
        with self._connection() as connection:
            connection.execute("UPDATE notification_events SET delivery_status=? WHERE id=?", (status, event_id))

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
        connection.execute("PRAGMA foreign_keys = ON")
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


def _event_row(row: sqlite3.Row) -> NotificationEvent:
    return NotificationEvent(int(row["id"]), int(row["reminder_id"]), row["title"], datetime.fromisoformat(row["triggered_at"]), datetime.fromisoformat(row["read_at"]) if row["read_at"] else None, row["delivery_status"])
