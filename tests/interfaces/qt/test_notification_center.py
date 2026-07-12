from datetime import datetime, timedelta, timezone

from lina.interfaces.qt.notification_center import NotificationCenterDialog
from lina.notifications.repository import NotificationRepository
from lina.notifications.service import NotificationService
from lina.interfaces.qt.reminder_dialog import ReminderDialog
from lina.notifications.models import ReminderStatus


def test_notification_center_renders_empty_state(qtbot, tmp_path) -> None:
    service = NotificationService(NotificationRepository(tmp_path / "notifications.sqlite3"))
    dialog = NotificationCenterDialog(service)
    qtbot.addWidget(dialog)

    assert dialog._items.count() == 1
    assert "Henüz" in dialog._items.item(0).text()


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
