from datetime import datetime, timezone, timedelta

from lina.notifications.models import ReminderRecurrence
from lina.notifications.repository import NotificationRepository
from lina.notifications.scheduler import FakeClock, NotificationScheduler
from lina.notifications.service import NotificationService, next_occurrence


def test_scheduler_detects_due_once_and_ignores_presenter_failure(tmp_path) -> None:
    clock = FakeClock(datetime(2026, 7, 12, 12, tzinfo=timezone.utc))
    service = NotificationService(NotificationRepository(tmp_path / "notifications.sqlite3"))
    reminder = service.create("Test", clock.now() - timedelta(minutes=1))
    delivered = []
    scheduler = NotificationScheduler(service._repository, lambda item: delivered.append(item), clock)

    assert scheduler.check_once() == (reminder,)
    assert scheduler.check_once() == ()
    assert delivered == [reminder]


def test_daily_and_weekly_next_occurrence() -> None:
    due = datetime(2026, 7, 12, tzinfo=timezone.utc)
    from lina.notifications.models import Reminder
    assert next_occurrence(Reminder(None, "daily", due, ReminderRecurrence.DAILY)) == due + timedelta(days=1)
    assert next_occurrence(Reminder(None, "weekly", due, ReminderRecurrence.WEEKLY)) == due + timedelta(days=7)
