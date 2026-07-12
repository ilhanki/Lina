from datetime import datetime, timezone

from lina.interfaces.qt.notification_center import NotificationCenterDialog
from lina.notifications.repository import NotificationRepository
from lina.notifications.service import NotificationService


def test_notification_center_renders_empty_state(qtbot, tmp_path) -> None:
    service = NotificationService(NotificationRepository(tmp_path / "notifications.sqlite3"))
    dialog = NotificationCenterDialog(service)
    qtbot.addWidget(dialog)

    assert dialog._items.count() == 1
    assert "Henüz" in dialog._items.item(0).text()
