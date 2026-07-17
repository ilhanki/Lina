"""Accessible timeline card for tool status and confirmation."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from lina.brain.routing.models import ToolStatus


STATUS_LABELS = {
    ToolStatus.PREPARING: "Hazırlanıyor",
    ToolStatus.AWAITING_CONFIRMATION: "Onay bekleniyor",
    ToolStatus.RUNNING: "Çalışıyor",
    ToolStatus.SUCCESS: "Tamamlandı",
    ToolStatus.FAILURE: "Başarısız",
    ToolStatus.CANCELLED: "İptal edildi",
    ToolStatus.UNAVAILABLE: "Kullanılamıyor",
}
STATUS_MARKS = {
    ToolStatus.PREPARING: "•",
    ToolStatus.AWAITING_CONFIRMATION: "?",
    ToolStatus.RUNNING: "•",
    ToolStatus.SUCCESS: "✓",
    ToolStatus.FAILURE: "×",
    ToolStatus.CANCELLED: "–",
    ToolStatus.UNAVAILABLE: "!",
}


class ToolActivityCard(QFrame):
    confirmed = Signal()
    cancelled = Signal()
    retry_requested = Signal()

    def __init__(self, title: str, description: str, arguments: str = "", risk: str = "Düşük", confirmation: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("toolActivityCard")
        self.setAccessibleName(f"Araç işlemi: {title}")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(9)
        self._title = QLabel(title, self); self._title.setObjectName("toolActivityTitle"); layout.addWidget(self._title)
        self._status = QLabel("", self); self._status.setAccessibleName("İşlem durumu"); layout.addWidget(self._status)
        self._description = QLabel(description, self); self._description.setWordWrap(True); layout.addWidget(self._description)
        self._arguments = QLabel(arguments, self); self._arguments.setObjectName("toolActivityDetails"); self._arguments.setWordWrap(True); self._arguments.hide(); layout.addWidget(self._arguments)
        self._risk = QLabel(f"Risk: {risk}", self); self._risk.setObjectName("toolActivityRisk"); layout.addWidget(self._risk)
        actions = QHBoxLayout()
        self.confirm_button = QPushButton("Onayla", self); self.confirm_button.setAccessibleName("İşlemi onayla"); self.confirm_button.clicked.connect(self.confirmed); actions.addWidget(self.confirm_button)
        self.cancel_button = QPushButton("Vazgeç", self); self.cancel_button.setAccessibleName("İşlemden vazgeç"); self.cancel_button.clicked.connect(self.cancelled); actions.addWidget(self.cancel_button)
        self.retry_button = QPushButton("Tekrar Dene", self); self.retry_button.setAccessibleName("İşlemi tekrar dene"); self.retry_button.clicked.connect(self.retry_requested); self.retry_button.hide(); actions.addWidget(self.retry_button)
        self.details_button = QPushButton("Ayrıntıları Göster", self); self.details_button.setObjectName("secondaryButton"); self.details_button.setAccessibleName("Araç ayrıntılarını göster veya gizle"); self.details_button.clicked.connect(self._toggle_details); self.details_button.setVisible(bool(arguments)); actions.addWidget(self.details_button)
        layout.addLayout(actions)
        self.confirm_button.setVisible(confirmation); self.cancel_button.setVisible(confirmation)
        self.set_status(ToolStatus.AWAITING_CONFIRMATION if confirmation else ToolStatus.PREPARING)

    def set_status(self, status: ToolStatus, summary: str = "", retryable: bool = False) -> None:
        status_names = {
            ToolStatus.SUCCESS: "toolStatusSuccess",
            ToolStatus.FAILURE: "toolStatusFailure",
            ToolStatus.CANCELLED: "toolStatusWarning",
            ToolStatus.UNAVAILABLE: "toolStatusWarning",
        }
        self._status.setObjectName(status_names.get(status, "toolStatusInfo"))
        self._status.style().unpolish(self._status)
        self._status.style().polish(self._status)
        self._status.setText(f"Durum: {STATUS_MARKS[status]} {STATUS_LABELS[status]}")
        if summary:
            self._description.setText(summary)
        confirmation = status is ToolStatus.AWAITING_CONFIRMATION
        self.confirm_button.setVisible(confirmation); self.cancel_button.setVisible(confirmation)
        self.retry_button.setVisible(retryable and status in {ToolStatus.FAILURE, ToolStatus.UNAVAILABLE})
        if confirmation:
            self.confirm_button.setDefault(True); self.confirm_button.setFocus()

    def _toggle_details(self) -> None:
        visible = not self._arguments.isVisible()
        self._arguments.setVisible(visible)
        self.details_button.setText("Ayrıntıları Gizle" if visible else "Ayrıntıları Göster")

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and self.confirm_button.isVisible():
            self.confirmed.emit(); return
        if event.key() == Qt.Key.Key_Escape and self.cancel_button.isVisible():
            self.cancelled.emit(); return
        super().keyPressEvent(event)
