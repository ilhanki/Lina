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


def test_event_lifecycle_duplicate_guard_and_delivery(tmp_path) -> None:
    repository = NotificationRepository(tmp_path / "notifications.sqlite3")
    reminder = repository.create(Reminder(None, "Bildirim", datetime.now(timezone.utc)))
    triggered = reminder.due_at
    event = repository.create_event(reminder, triggered)

    assert event is not None
    assert repository.create_event(reminder, triggered) is None
    assert repository.unread_event_count() == 1
    repository.update_delivery_status(event.id, "delivered")
    assert repository.list_events()[0].delivery_status == "delivered"
    repository.mark_event_read(event.id)
    assert repository.unread_event_count() == 0


def test_mark_all_events_read(tmp_path) -> None:
    repository = NotificationRepository(tmp_path / "notifications.sqlite3")
    reminder = repository.create(Reminder(None, "Bir", datetime.now(timezone.utc)))
    repository.create_event(reminder, reminder.due_at)
    repository.create_event(reminder, reminder.due_at.replace(microsecond=1))
    repository.mark_all_events_read()
    assert repository.unread_event_count() == 0
