from datetime import datetime, timezone

from lina.notifications.models import Reminder, ReminderRecurrence
from lina.notifications.repository import NotificationRepository


def test_repository_creates_and_lists_reminders(tmp_path) -> None:
    repository = NotificationRepository(tmp_path / "notifications.sqlite3")
    due_at = datetime(2026, 7, 12, 12, tzinfo=timezone.utc)

    created = repository.create(Reminder(None, "Toplantı", due_at, ReminderRecurrence.DAILY))

    reminders = repository.list()
    assert reminders[0].id == created.id
    assert reminders[0].recurrence is ReminderRecurrence.DAILY
    assert reminders[0].due_at == due_at


def test_repository_updates_without_sharing_connections(tmp_path) -> None:
    repository = NotificationRepository(tmp_path / "notifications.sqlite3")
    created = repository.create(Reminder(None, "Hatırlatıcı", datetime.now(timezone.utc)))

    updated = repository.update(Reminder(created.id, "Güncellendi", created.due_at))

    assert repository.list()[0].title == updated.title
