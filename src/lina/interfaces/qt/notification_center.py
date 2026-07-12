"""Notification Center dialog for local reminders."""

from PySide6.QtWidgets import QDialog, QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout

from lina.notifications.models import Reminder, ReminderStatus
from lina.notifications.service import NotificationService


class NotificationCenterDialog(QDialog):
    """Display reminder status without exposing persistence details."""

    def __init__(self, service: NotificationService, parent=None) -> None:
        super().__init__(parent)
        self._service = service
        self.setWindowTitle("Bildirimler")
        self.setMinimumSize(460, 480)
        self.resize(560, 620)
        layout = QVBoxLayout(self)
        self._filter = QListWidget(self)
        self._filter.addItems(["Tümü", "Bekleyen", "Tamamlanan"])
        self._filter.currentRowChanged.connect(lambda _row: self.refresh())
        layout.addWidget(self._filter)
        self._items = QListWidget(self)
        layout.addWidget(self._items, 1)
        self._mark_all = QPushButton("Tümünü Okundu İşaretle", self)
        layout.addWidget(self._mark_all)
        self._mark_all.clicked.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        self._items.clear()
        reminders = self._service.list()
        mode = self._filter.currentRow()
        for reminder in reminders:
            if mode == 1 and reminder.status is not ReminderStatus.ACTIVE:
                continue
            if mode == 2 and reminder.status is not ReminderStatus.COMPLETED:
                continue
            item = QListWidgetItem(f"{reminder.title} · {reminder.due_at.astimezone().strftime('%d.%m %H:%M')}")
            self._items.addItem(item)
        if not self._items.count():
            self._items.addItem("Henüz hatırlatıcın yok.")
