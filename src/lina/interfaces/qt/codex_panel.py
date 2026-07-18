"""Compact Codex inspector, approval card, progress, and metadata history."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget

from lina.codex.models import CodexHistoryEntry, CodexSession, CodexSessionStatus


class CodexInspector(QWidget):
    approve_requested = Signal()
    deny_requested = Signal()
    edit_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("codexInspector")
        layout = QVBoxLayout(self)
        self.task_label = QLabel("Aktif Codex görevi yok.", self)
        self.task_label.setObjectName("codexActiveTask")
        self.status_label = QLabel("Durum · Hazır", self)
        self.workspace_label = QLabel("Workspace · Seçilmedi", self)
        self.progress = QProgressBar(self)
        self.progress.setRange(0, 100)
        self.progress.setAccessibleName("Codex görev ilerlemesi")
        self.approval_card = QWidget(self)
        self.approval_card.setObjectName("codexApprovalCard")
        approval_layout = QVBoxLayout(self.approval_card)
        self.approval_summary = QLabel("Bu değişiklik uygulanmadan önce onayın gerekiyor.", self.approval_card)
        self.approval_summary.setWordWrap(True)
        self.approve_button = QPushButton("Onayla", self.approval_card)
        self.deny_button = QPushButton("Reddet", self.approval_card)
        self.edit_button = QPushButton("Düzenle", self.approval_card)
        approval_layout.addWidget(self.approval_summary)
        for button in (self.approve_button, self.deny_button, self.edit_button):
            approval_layout.addWidget(button)
        self.approve_button.clicked.connect(self.approve_requested)
        self.deny_button.clicked.connect(self.deny_requested)
        self.edit_button.clicked.connect(self.edit_requested)
        self.history_label = QLabel("Geçmiş · Henüz görev yok", self)
        self.history_label.setObjectName("codexHistory")
        self.history_label.setWordWrap(True)
        for widget in (self.task_label, self.status_label, self.workspace_label,
                       self.progress, self.approval_card, self.history_label):
            layout.addWidget(widget)
        self.render(None)

    def render(self, session: CodexSession | None,
               history: tuple[CodexHistoryEntry, ...] = ()) -> None:
        active = session is not None and not session.terminal
        self.setVisible(active or bool(history))
        if session is None:
            self.task_label.setText("Aktif Codex görevi yok.")
            self.status_label.setText("Durum · Hazır")
            self.workspace_label.setText("Workspace · Seçilmedi")
            self.progress.setValue(0)
            waiting = False
        else:
            self.task_label.setText(f"Aktif görev · {session.task_summary}")
            self.status_label.setText(f"Durum · {session.status.value}")
            self.workspace_label.setText(f"Workspace · {session.project_context.root_path.name}")
            self.progress.setValue(session.progress)
            waiting = session.status is CodexSessionStatus.WAITING_APPROVAL
            if session.task is not None:
                targets = ", ".join(action.target for action in session.task.requested_actions if action.target)
                self.approval_summary.setText(
                    f"Amaç: {session.task.objective}\nRisk: {session.task.risk_level.value}"
                    + (f"\nDosya: {targets}" if targets else ""))
        self.approval_card.setVisible(waiting)
        summaries = [f"{item.created_at.date()} · {item.task_summary} · {item.status.value}"
                     for item in history[:5]]
        self.history_label.setText("Geçmiş\n" + "\n".join(summaries)
                                   if summaries else "Geçmiş · Henüz görev yok")
