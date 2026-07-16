from datetime import datetime, timedelta, timezone

from lina.interfaces.qt.notification_center import NotificationCenterDialog
from lina.notifications.repository import NotificationRepository
from lina.notifications.service import NotificationService
from lina.interfaces.qt.reminder_dialog import ReminderDialog
from lina.notifications.models import ReminderStatus
from lina.notifications.models import ReminderRecurrence
import lina.interfaces.qt.notification_center as notification_center_module
import lina.interfaces.qt.main_window as main_window_module
from lina.interfaces.qt.main_window import LinaMainWindow
from lina.settings.repository import UserSettingsRepository
from lina.settings.service import UserSettingsService
from lina.interfaces.qt.theme import build_stylesheet


def test_notification_center_renders_empty_state(qtbot, tmp_path) -> None:
    service = NotificationService(NotificationRepository(tmp_path / "notifications.sqlite3"))
    dialog = NotificationCenterDialog(service)
    qtbot.addWidget(dialog)

    assert dialog._items.count() == 1
    assert "Henüz" in dialog._items.item(0).text()
    dialog.setStyleSheet(build_stylesheet("Segoe UI", "light", 1.35))
    assert dialog.objectName() == "notificationCenter"
    assert dialog._filter.objectName() == "notificationFilter"
    assert dialog._items.objectName() == "notificationItems"


def test_notification_center_complete_snooze_and_mark_read(qtbot, tmp_path) -> None:
    service = NotificationService(NotificationRepository(tmp_path / "notifications.sqlite3"))
    reminder = service.create("Toplantı", datetime.now(timezone.utc) + timedelta(days=1))
    event = service._repository.create_event(reminder, reminder.due_at)
    dialog = NotificationCenterDialog(service)
    qtbot.addWidget(dialog)
    dialog._items.setCurrentRow(0)
    dialog.snooze_selected()
    assert service.list()[0].due_at == reminder.due_at + timedelta(minutes=10)
    dialog._items.setCurrentRow(0)
    dialog.complete_selected()
    assert service.list()[0].status is ReminderStatus.COMPLETED
    service.mark_read(event.id)
    assert service.unread_count() == 0


def test_reminder_dialog_shows_turkish_validation(qtbot) -> None:
    dialog = ReminderDialog()
    qtbot.addWidget(dialog)
    dialog.title_edit.clear()
    dialog._validate()
    assert "Başlık" in dialog.error_label.text()
    dialog.title_edit.setText("Geçmiş")
    dialog.due_edit.setDateTime(datetime.now().astimezone() - timedelta(minutes=1))
    dialog._validate()
    assert "gelecekte" in dialog.error_label.text()


def test_reminder_dialog_returns_recurrence_enum_and_service_persists_it(qtbot, tmp_path) -> None:
    dialog = ReminderDialog()
    qtbot.addWidget(dialog)
    dialog.recurrence_combo.setCurrentIndex(1)
    service = NotificationService(NotificationRepository(tmp_path / "notifications.sqlite3"))

    assert dialog.recurrence is ReminderRecurrence.DAILY
    created = service.create("Günlük", dialog.due_at, dialog.recurrence_combo.currentData())
    assert created.recurrence is ReminderRecurrence.DAILY
    assert service.list()[0].recurrence is ReminderRecurrence.DAILY


class _TextValue:
    def __init__(self, value: str) -> None:
        self._value = value

    def text(self) -> str:
        return self._value


class _AcceptedReminderDialog:
    due_at = datetime.now(timezone.utc) + timedelta(hours=2)
    recurrence = ReminderRecurrence.NONE

    def __init__(self, parent=None) -> None:
        self.title_edit = _TextValue("Yeni reminder")

    def exec(self) -> int:
        return 1


def test_create_calls_service_and_reloads_pending_list(qtbot, tmp_path, monkeypatch) -> None:
    service = NotificationService(NotificationRepository(tmp_path / "notifications.sqlite3"))
    dialog = NotificationCenterDialog(service)
    qtbot.addWidget(dialog)
    calls = []
    original_create = service.create

    def create(*args, **kwargs):
        calls.append((args, kwargs))
        return original_create(*args, **kwargs)

    monkeypatch.setattr(service, "create", create)
    monkeypatch.setattr(notification_center_module, "ReminderDialog", _AcceptedReminderDialog)

    dialog.create_reminder()

    assert len(calls) == 1
    assert dialog._filter.currentText() == "Yaklaşanlar"
    assert dialog._items.count() == 1
    assert "Yeni reminder" in dialog._items.item(0).text()
    assert service.unread_count() == 0


def test_center_reopen_and_restart_reload_persisted_reminder(qtbot, tmp_path) -> None:
    database = tmp_path / "notifications.sqlite3"
    service = NotificationService(NotificationRepository(database))
    service.create("Kalıcı reminder", datetime.now(timezone.utc) + timedelta(days=1))

    first = NotificationCenterDialog(service)
    qtbot.addWidget(first)
    first.close()
    restarted_service = NotificationService(NotificationRepository(database))
    reopened = NotificationCenterDialog(restarted_service)
    qtbot.addWidget(reopened)

    assert "Kalıcı reminder" in reopened._items.item(0).text()


def test_local_due_time_round_trip_stays_in_upcoming_filter(qtbot, tmp_path) -> None:
    service = NotificationService(NotificationRepository(tmp_path / "notifications.sqlite3"))
    local_due = datetime.now().astimezone() + timedelta(hours=1)
    created = service.create("Yerel saat", local_due)
    dialog = NotificationCenterDialog(service)
    qtbot.addWidget(dialog)

    assert created.due_at == local_due.astimezone(timezone.utc)
    assert "Yerel saat" in dialog._items.item(0).text()
    dialog._filter.setCurrentIndex(1)
    assert "Yerel saat" not in dialog._items.item(0).text()


class _ConversationService:
    pass


def test_main_window_create_refreshes_open_center_without_badge_increment(qtbot, tmp_path, monkeypatch) -> None:
    service = NotificationService(NotificationRepository(tmp_path / "notifications.sqlite3"))
    settings = UserSettingsService(UserSettingsRepository(tmp_path / "user-settings.json"))
    window = LinaMainWindow(
        _ConversationService(),
        user_settings_service=settings,
        notification_service=service,
    )
    qtbot.addWidget(window)
    window.open_notifications()
    monkeypatch.setattr(main_window_module, "ReminderDialog", _AcceptedReminderDialog)

    window.create_reminder()

    assert "Yeni reminder" in window._notification_dialog._items.item(0).text()
    assert window._notification_button.text() == ""
    assert not window._notification_button.icon().isNull()
    window._force_exit = True
    window.close()


def test_open_existing_center_reloads_database(qtbot, tmp_path) -> None:
    service = NotificationService(NotificationRepository(tmp_path / "notifications.sqlite3"))
    window = LinaMainWindow(_ConversationService(), notification_service=service)
    qtbot.addWidget(window)
    window.open_notifications()
    service.create("Dışarıdan eklendi", datetime.now(timezone.utc) + timedelta(hours=3))

    window.open_notifications()

    assert "Dışarıdan eklendi" in window._notification_dialog._items.item(0).text()
    window._force_exit = True
    window.close()
