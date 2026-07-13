"""Notification Center dialog for local reminders."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone

from PySide6.QtWidgets import QComboBox, QDialog, QHBoxLayout, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QVBoxLayout

from lina.interfaces.qt.reminder_dialog import ReminderDialog
from lina.notifications.models import Reminder, ReminderStatus
from lina.notifications.service import NotificationService


class NotificationCenterDialog(QDialog):
    def __init__(self, service: NotificationService, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("notificationCenter")
        self._service = service
        self.setWindowTitle("Bildirimler")
        self.setMinimumSize(560, 520)
        layout = QVBoxLayout(self)
        self._filter = QComboBox(self)
        self._filter.setObjectName("notificationFilter")
        self._filter.addItems(["Yaklaşanlar", "Geçmiş", "Tamamlananlar"])
        self._filter.currentIndexChanged.connect(self.refresh)
        layout.addWidget(self._filter)
        self._items = QListWidget(self)
        self._items.setObjectName("notificationItems")
        layout.addWidget(self._items, 1)
        actions = QHBoxLayout()
        for text, handler in (("Yeni", self.create_reminder), ("Düzenle", self.edit_selected), ("Tamamla", self.complete_selected), ("Sil", self.delete_selected)):
            button = QPushButton(text, self); button.clicked.connect(handler); actions.addWidget(button)
        self._snooze = QComboBox(self)
        self._snooze.addItems(["10 dakika ertele", "1 saat ertele", "Yarın aynı saat"])
        actions.addWidget(self._snooze)
        snooze_button = QPushButton("Ertele", self); snooze_button.clicked.connect(self.snooze_selected); actions.addWidget(snooze_button)
        layout.addLayout(actions)
        read_actions = QHBoxLayout()
        mark = QPushButton("Okundu İşaretle", self); mark.clicked.connect(self.mark_selected_read); read_actions.addWidget(mark)
        self._mark_all = QPushButton("Tümünü Okundu İşaretle", self); self._mark_all.clicked.connect(self.mark_all_read); read_actions.addWidget(self._mark_all)
        layout.addLayout(read_actions)
        self.reload()

    def refresh(self, *_args) -> None:
        self.reload()

    def reload(self, select_reminder_id: int | None = None) -> None:
        """Reload reminders from SQLite and optionally select a newly saved row."""
        self._items.clear()
        now = datetime.now(timezone.utc)
        reminders = self._service.list()
        mode = self._filter.currentIndex()
        selected = [r for r in reminders if self._matches_filter(r, mode, now)]
        for reminder in selected:
            item = QListWidgetItem(f"{reminder.title} · {reminder.due_at.astimezone().strftime('%d.%m.%Y %H:%M')}")
            item.setData(256, reminder)
            self._items.addItem(item)
            if reminder.id == select_reminder_id:
                self._items.setCurrentItem(item)
        if not selected:
            labels = ("Henüz yaklaşan hatırlatıcı yok.", "Henüz geçmiş hatırlatıcı yok.", "Henüz tamamlanan hatırlatıcı yok.")
            self._items.addItem(QListWidgetItem(labels[mode]))

    @staticmethod
    def _matches_filter(reminder: Reminder, mode: int, now: datetime) -> bool:
        due_at = reminder.due_at.astimezone(timezone.utc)
        return (
            (mode == 0 and reminder.status is ReminderStatus.ACTIVE and due_at > now)
            or (mode == 1 and reminder.status is ReminderStatus.ACTIVE and due_at <= now)
            or (mode == 2 and reminder.status is ReminderStatus.COMPLETED)
        )

    def _selected(self) -> Reminder | None:
        item = self._items.currentItem()
        return item.data(256) if item else None

    def create_reminder(self) -> None:
        dialog = ReminderDialog(parent=self)
        if not dialog.exec():
            return
        created = self._service.create(
            dialog.title_edit.text().strip(), dialog.due_at, dialog.recurrence
        )
        self._filter.setCurrentIndex(0)
        self.reload(created.id)

    def edit_selected(self) -> None:
        reminder = self._selected()
        if not reminder: return
        dialog = ReminderDialog(reminder, self)
        if dialog.exec(): self._service.update(replace(reminder, title=dialog.title_edit.text().strip(), due_at=dialog.due_at, recurrence=dialog.recurrence)); self.refresh()

    def complete_selected(self) -> None:
        reminder = self._selected()
        if reminder: self._service.complete(reminder); self.refresh()

    def delete_selected(self) -> None:
        reminder = self._selected()
        if reminder and QMessageBox.question(self, "Hatırlatıcıyı Sil", "Bu hatırlatıcı silinsin mi?") == QMessageBox.StandardButton.Yes:
            self._service.delete(reminder); self.refresh()

    def snooze_selected(self) -> None:
        reminder = self._selected()
        if not reminder: return
        if self._snooze.currentIndex() == 0: self._service.snooze(reminder, timedelta(minutes=10))
        elif self._snooze.currentIndex() == 1: self._service.snooze(reminder, timedelta(hours=1))
        else: self._service.snooze_tomorrow(reminder)
        self.refresh()

    def mark_selected_read(self) -> None:
        reminder = self._selected()
        if reminder:
            for event in self._service.events():
                if event.reminder_id == reminder.id and event.read_at is None: self._service.mark_read(event.id or 0)

    def mark_all_read(self) -> None:
        self._service.mark_all_read()
