from datetime import datetime, timezone, timedelta
from types import SimpleNamespace

from lina.notifications.models import Reminder, ReminderRecurrence
from lina.notifications.repository import NotificationRepository
from lina.notifications.scheduler import FakeClock, NotificationScheduler
from lina.notifications.service import NotificationService, next_occurrence


def test_scheduler_detects_due_once_and_ignores_presenter_failure(tmp_path) -> None:
    clock = FakeClock(datetime(2026, 7, 12, 12, tzinfo=timezone.utc))
    service = NotificationService(NotificationRepository(tmp_path / "notifications.sqlite3"))
    reminder = service._repository.create(Reminder(None, "Test", clock.now() - timedelta(minutes=1)))
    delivered = []
    scheduler = NotificationScheduler(service._repository, lambda item: delivered.append(item) or "delivered", clock)

    assert scheduler.check_once() == (reminder,)
    assert scheduler.check_once() == ()
    assert [event.title for event in delivered] == [reminder.title]


def test_daily_and_weekly_next_occurrence() -> None:
    due = datetime(2026, 7, 12, tzinfo=timezone.utc)
    assert next_occurrence(Reminder(None, "daily", due, ReminderRecurrence.DAILY)) == due + timedelta(days=1)
    assert next_occurrence(Reminder(None, "weekly", due, ReminderRecurrence.WEEKLY)) == due + timedelta(days=7)


def _settings(**overrides):
    values = dict(reminders_enabled=True, desktop_notifications_enabled=True, show_missed_reminders=True)
    values.update(overrides)
    return SimpleNamespace(**values)


def test_future_ignored_and_reminders_disabled(tmp_path) -> None:
    clock = FakeClock(datetime(2026, 7, 12, 12, tzinfo=timezone.utc))
    repository = NotificationRepository(tmp_path / "n.sqlite3")
    repository.create(Reminder(None, "Future", clock.now() + timedelta(minutes=1)))
    scheduler = NotificationScheduler(repository, lambda _event: "delivered", clock, settings_provider=lambda: _settings(reminders_enabled=False))
    assert scheduler.check_once() == ()
    assert repository.list_events() == ()


def test_desktop_disabled_persists_suppressed_event(tmp_path) -> None:
    clock = FakeClock(datetime(2026, 7, 12, 12, tzinfo=timezone.utc))
    repository = NotificationRepository(tmp_path / "n.sqlite3")
    repository.create(Reminder(None, "Due", clock.now() - timedelta(minutes=1)))
    scheduler = NotificationScheduler(repository, lambda _event: (_ for _ in ()).throw(AssertionError()), clock, settings_provider=lambda: _settings(desktop_notifications_enabled=False))
    assert len(scheduler.check_once()) == 1
    assert repository.list_events()[0].delivery_status == "suppressed"


def test_missed_recurrence_collapses_and_advances_to_future(tmp_path) -> None:
    clock = FakeClock(datetime(2026, 7, 12, 12, tzinfo=timezone.utc))
    repository = NotificationRepository(tmp_path / "n.sqlite3")
    for index in range(4):
        repository.create(Reminder(None, f"Missed {index}", clock.now() - timedelta(days=10), ReminderRecurrence.DAILY if index == 0 else ReminderRecurrence.NONE))
    shown = []
    scheduler = NotificationScheduler(repository, lambda event: shown.append(event) or "delivered", clock, settings_provider=lambda: _settings())
    assert len(scheduler.process_missed()) == 4
    assert [event.title for event in shown] == ["4 kaçırılmış hatırlatıcın var"]
    assert next(item for item in repository.list() if item.title == "Missed 0").due_at > clock.now()
    assert len(repository.list_events()) == 4


def test_show_missed_disabled_keeps_events_without_popup(tmp_path) -> None:
    clock = FakeClock(datetime(2026, 7, 12, 12, tzinfo=timezone.utc))
    repository = NotificationRepository(tmp_path / "n.sqlite3")
    repository.create(Reminder(None, "Missed", clock.now() - timedelta(days=1)))
    scheduler = NotificationScheduler(repository, lambda _event: (_ for _ in ()).throw(AssertionError()), clock, settings_provider=lambda: _settings(show_missed_reminders=False))
    scheduler.process_missed()
    assert repository.list_events()[0].delivery_status == "suppressed"


def test_presenter_and_persistence_failures_do_not_escape(tmp_path) -> None:
    clock = FakeClock(datetime(2026, 7, 12, 12, tzinfo=timezone.utc))
    repository = NotificationRepository(tmp_path / "n.sqlite3")
    repository.create(Reminder(None, "Due", clock.now() - timedelta(minutes=1)))
    scheduler = NotificationScheduler(repository, lambda _event: (_ for _ in ()).throw(RuntimeError("tray")), clock)
    assert len(scheduler.check_once()) == 1
    assert repository.list_events()[0].delivery_status == "failed"


def test_clean_shutdown_is_idempotent(tmp_path) -> None:
    scheduler = NotificationScheduler(NotificationRepository(tmp_path / "n.sqlite3"), lambda _event: "delivered", interval_seconds=3600)
    scheduler.start(); scheduler.start(); scheduler.stop(); scheduler.stop()
    assert scheduler._thread is None
    assert scheduler.check_once() == ()
