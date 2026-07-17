"""Compact, accessible Agent Mode plan and progress panel."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget

from lina.agent.models import AgentSession, AgentSessionStatus, AgentStepStatus


STATUS_LABELS = {
    AgentStepStatus.PENDING: "○ Bekliyor",
    AgentStepStatus.WAITING_APPROVAL: "! Onay bekliyor",
    AgentStepStatus.RUNNING: "▶ Çalışıyor",
    AgentStepStatus.VERIFYING: "◇ Doğrulanıyor",
    AgentStepStatus.SUCCEEDED: "✓ Tamamlandı",
    AgentStepStatus.FAILED: "× Başarısız",
    AgentStepStatus.SKIPPED: "↷ Atlandı",
    AgentStepStatus.CANCELLED: "■ İptal edildi",
    AgentStepStatus.BLOCKED: "! Engellendi",
}
SESSION_STATUS_LABELS = {
    AgentSessionStatus.IDLE: "Hazırlanıyor",
    AgentSessionStatus.PLANNING: "Planlanıyor",
    AgentSessionStatus.AWAITING_INPUT: "Bilgi bekliyor",
    AgentSessionStatus.AWAITING_PLAN_APPROVAL: "Plan onayı bekliyor",
    AgentSessionStatus.READY: "Başlamaya hazır",
    AgentSessionStatus.RUNNING: "Çalışıyor",
    AgentSessionStatus.PAUSED: "Duraklatıldı",
    AgentSessionStatus.AWAITING_STEP_APPROVAL: "Adım onayı bekliyor",
    AgentSessionStatus.REPLANNING: "Plan güncelleniyor",
    AgentSessionStatus.COMPLETED: "Tamamlandı",
    AgentSessionStatus.PARTIALLY_COMPLETED: "Kısmen tamamlandı",
    AgentSessionStatus.FAILED: "Başarısız",
    AgentSessionStatus.CANCELLED: "İptal edildi",
    AgentSessionStatus.BLOCKED: "Engellendi",
    AgentSessionStatus.INTERRUPTED: "Yarım kaldı",
    AgentSessionStatus.UNCERTAIN: "Sonuç belirsiz",
}
RISK_LABELS = {
    "read_only": "Salt okunur",
    "low": "Düşük",
    "persistent": "Kalıcı",
    "sensitive": "Hassas",
    "prohibited": "Yasak",
}


class AgentPanel(QWidget):
    mode_toggle_requested = Signal()
    start_requested = Signal()
    approve_requested = Signal()
    skip_requested = Signal()
    modify_requested = Signal()
    pause_requested = Signal()
    resume_requested = Signal()
    cancel_requested = Signal()
    details_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("agentPanel")
        self.setAccessibleName("Agent Mode görev paneli")
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 7, 10, 7)
        header = QHBoxLayout()
        self.mode_label = QPushButton("Agent Mode · Kapalı", self)
        self.mode_label.setObjectName("statusChip")
        self.mode_label.clicked.connect(self.mode_toggle_requested.emit)
        self.progress_label = QLabel("Aktif görev yok", self)
        self.progress_label.setObjectName("mutedLabel")
        header.addWidget(self.mode_label)
        header.addWidget(self.progress_label, 1)
        self.details_button = QPushButton("Ayrıntıları Göster", self)
        self._details_expanded = False
        self.details_button.clicked.connect(self._toggle_details)
        self.details_button.clicked.connect(self.details_requested.emit)
        header.addWidget(self.details_button)
        root.addLayout(header)
        self.summary_label = QLabel("", self)
        self.summary_label.setWordWrap(True)
        root.addWidget(self.summary_label)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setObjectName("agentProgress")
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setAccessibleName("Agent görev ilerlemesi")
        root.addWidget(self.progress_bar)
        self.steps_label = QLabel("", self)
        self.steps_label.setWordWrap(True)
        self.steps_label.setTextInteractionFlags(self.steps_label.textInteractionFlags())
        self.steps_label.hide()
        root.addWidget(self.steps_label)
        actions = QHBoxLayout()
        self.start_button = self._button("Planı Başlat", self.start_requested, actions)
        self.approve_button = self._button("Onayla", self.approve_requested, actions)
        self.skip_button = self._button("Atla", self.skip_requested, actions)
        self.modify_button = self._button("Planı Düzenle", self.modify_requested, actions)
        self.pause_button = self._button("Duraklat", self.pause_requested, actions)
        self.resume_button = self._button("Devam Et", self.resume_requested, actions)
        self.cancel_button = self._button("İptal", self.cancel_requested, actions)
        root.addLayout(actions)
        self.render(None, enabled=False)

    def _button(self, text, signal, layout):
        button = QPushButton(text, self)
        button.clicked.connect(signal.emit)
        layout.addWidget(button)
        return button

    def render(self, session: AgentSession | None, *, enabled: bool) -> None:
        self.mode_label.setText(f"Agent Mode · {'Açık' if enabled else 'Kapalı'}")
        if session is None:
            self.progress_label.setText("Aktif görev yok")
            self.summary_label.setText("Agent Mode yalnızca açıkça istendiğinde plan hazırlar.")
            self.steps_label.setText("")
            self.progress_bar.setRange(0, 1)
            self.progress_bar.setValue(0)
            self._set_actions()
            return
        plan = session.plan
        total = len(plan.steps) if plan else 0
        current = min(session.current_step_index + (0 if session.terminal else 1), total)
        self.progress_bar.setRange(0, max(1, total))
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"{SESSION_STATUS_LABELS[session.status]} · {current}/{total}")
        if plan:
            persistent = any(step.risk_level.value in {"persistent", "sensitive"} for step in plan.steps)
            self.summary_label.setText(
                f"{plan.summary} · {total} adım · Kalıcı işlem: {'Var; ayrı onay gerekir' if persistent else 'Yok'}"
            )
        else:
            self.summary_label.setText(session.last_summary or "Plan hazırlanıyor…")
        if plan:
            self.steps_label.setText("\n".join(
                f"{index}. {STATUS_LABELS[step.status]} · {step.title} · Araç: {step.tool_name} · Risk: {RISK_LABELS[step.risk_level.value]}"
                for index, step in enumerate(plan.steps, 1)
            ))
        self._set_actions(session.status)

    def _set_actions(self, status: AgentSessionStatus | None = None) -> None:
        self.start_button.setEnabled(status is AgentSessionStatus.AWAITING_PLAN_APPROVAL)
        waiting = status is AgentSessionStatus.AWAITING_STEP_APPROVAL
        self.approve_button.setEnabled(waiting)
        self.skip_button.setEnabled(waiting)
        self.modify_button.setEnabled(status in {AgentSessionStatus.AWAITING_PLAN_APPROVAL, AgentSessionStatus.AWAITING_STEP_APPROVAL})
        self.pause_button.setEnabled(status in {AgentSessionStatus.READY, AgentSessionStatus.RUNNING, AgentSessionStatus.AWAITING_STEP_APPROVAL})
        self.resume_button.setEnabled(status is AgentSessionStatus.PAUSED)
        self.cancel_button.setEnabled(status is not None and status not in {
            AgentSessionStatus.COMPLETED, AgentSessionStatus.PARTIALLY_COMPLETED,
            AgentSessionStatus.FAILED, AgentSessionStatus.CANCELLED, AgentSessionStatus.BLOCKED,
            AgentSessionStatus.INTERRUPTED, AgentSessionStatus.UNCERTAIN,
        })
        visibility = {
            self.start_button: status is AgentSessionStatus.AWAITING_PLAN_APPROVAL,
            self.approve_button: waiting,
            self.skip_button: waiting,
            self.modify_button: status in {AgentSessionStatus.AWAITING_PLAN_APPROVAL, AgentSessionStatus.AWAITING_STEP_APPROVAL},
            self.pause_button: status in {AgentSessionStatus.READY, AgentSessionStatus.RUNNING, AgentSessionStatus.AWAITING_STEP_APPROVAL},
            self.resume_button: status is AgentSessionStatus.PAUSED,
            self.cancel_button: status is not None and not (status in {
                AgentSessionStatus.COMPLETED, AgentSessionStatus.PARTIALLY_COMPLETED,
                AgentSessionStatus.FAILED, AgentSessionStatus.CANCELLED, AgentSessionStatus.BLOCKED,
                AgentSessionStatus.INTERRUPTED, AgentSessionStatus.UNCERTAIN,
            }),
        }
        for button, visible in visibility.items():
            button.setVisible(visible)

    def _toggle_details(self) -> None:
        self._details_expanded = not self._details_expanded
        self.steps_label.setVisible(self._details_expanded and bool(self.steps_label.text()))
        self.details_button.setText("Ayrıntıları Gizle" if self._details_expanded else "Ayrıntıları Göster")
