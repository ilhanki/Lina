"""Notification delivery boundaries."""

from __future__ import annotations

from typing import Protocol

from lina.notifications.models import NotificationEvent


class NotificationPresenter(Protocol):
    def present(self, event: NotificationEvent) -> str: ...


class InAppNotificationPresenter:
    """Fallback presenter that forwards events to an application callback."""

    def __init__(self, callback) -> None:
        self._callback = callback

    def present(self, event: NotificationEvent) -> str:
        self._callback(event)
        return "in_app"


class QtNotificationPresenter:
    """Best-effort tray presenter; Qt failures remain local to delivery."""

    def __init__(self, tray_icon) -> None:
        self._tray_icon = tray_icon

    def present(self, event: NotificationEvent) -> str:
        if self._tray_icon is None or not self._tray_icon.isVisible():
            return "in_app"
        try:
            self._tray_icon.showMessage("Lina", event.title)
            return "delivered"
        except Exception:
            return "failed"
