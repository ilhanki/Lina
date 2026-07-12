"""Create and edit reminder dialog."""

from datetime import datetime, timezone

from PySide6.QtCore import QDateTime
from PySide6.QtWidgets import QComboBox, QDateTimeEdit, QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit, QVBoxLayout

from lina.notifications.models import Reminder, ReminderRecurrence


class ReminderDialog(QDialog):
    def __init__(self, reminder: Reminder | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Hatırlatıcıyı Düzenle" if reminder else "Yeni Hatırlatıcı")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.title_edit = QLineEdit(reminder.title if reminder else "", self)
        self.due_edit = QDateTimeEdit(self)
        self.due_edit.setCalendarPopup(True)
        self.due_edit.setDisplayFormat("dd.MM.yyyy HH:mm")
        due = reminder.due_at.astimezone() if reminder else datetime.now().astimezone()
        if reminder is None:
            due = due.replace(second=0, microsecond=0)
            from datetime import timedelta
            due += timedelta(hours=1)
        self.due_edit.setDateTime(QDateTime.fromMSecsSinceEpoch(int(due.timestamp() * 1000)).toLocalTime())
        self.recurrence_combo = QComboBox(self)
        for label, value in (("Tekrarlama yok", ReminderRecurrence.NONE), ("Her gün", ReminderRecurrence.DAILY), ("Her hafta", ReminderRecurrence.WEEKLY)):
            self.recurrence_combo.addItem(label, value)
        if reminder:
            self.recurrence_combo.setCurrentIndex(self.recurrence_combo.findData(reminder.recurrence))
        form.addRow("Başlık", self.title_edit)
        form.addRow("Zaman", self.due_edit)
        form.addRow("Tekrar", self.recurrence_combo)
        layout.addLayout(form)
        self.error_label = QLabel("", self)
        self.error_label.setObjectName("errorLabel")
        layout.addWidget(self.error_label)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate(self) -> None:
        if not self.title_edit.text().strip():
            self.error_label.setText("Başlık boş bırakılamaz.")
            return
        if self.due_at <= datetime.now(timezone.utc):
            self.error_label.setText("Hatırlatma zamanı gelecekte olmalı.")
            return
        self.accept()

    @property
    def due_at(self) -> datetime:
        # QDateTimeEdit displays local wall time. Epoch conversion avoids treating
        # that wall time as UTC on systems whose local timezone is not UTC.
        milliseconds = self.due_edit.dateTime().toMSecsSinceEpoch()
        return datetime.fromtimestamp(milliseconds / 1000, tz=timezone.utc)

    @property
    def recurrence(self) -> ReminderRecurrence:
        return self.recurrence_combo.currentData()
