from datetime import datetime, timezone

from lina.notifications.models import NotificationEvent
from lina.notifications.presenter import InAppNotificationPresenter, QtNotificationPresenter


def test_in_app_presenter_forwards_event() -> None:
    events = []
    event = NotificationEvent(1, 2, "Hatırlatma", datetime.now(timezone.utc))

    assert InAppNotificationPresenter(events.append).present(event) == "in_app"
    assert events == [event]


def test_qt_presenter_falls_back_without_tray() -> None:
    event = NotificationEvent(1, 2, "Hatırlatma", datetime.now(timezone.utc))

    assert QtNotificationPresenter(None).present(event) == "in_app"
