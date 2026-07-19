"""Codex task center, setup, recovery and change review summary cards."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget

from lina.codex.changes import CodexChangeSet
from lina.codex.models import CodexHistoryEntry, CodexSession, CodexSessionStatus
from lina.codex.transports.diagnostics import CodexCliInfo


class CodexInspector(QWidget):
    approve_requested = Signal()
    deny_requested = Signal()
    edit_requested = Signal()
    workspace_select_requested = Signal()
    workspace_cancel_requested = Signal()
    refresh_requested = Signal()
    login_requested = Signal()
    device_login_requested = Signal()
    logout_requested = Signal()
    stop_requested = Signal()
    diagnostics_requested = Signal()
    installation_guide_requested = Signal()
    terminal_requested = Signal()
    review_requested = Signal()
    resume_requested = Signal()
    recovery_inspect_requested = Signal(object)
    recovery_restart_requested = Signal(object)
    recovery_remove_requested = Signal(object)

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

        self.setup_card = QWidget(self)
        self.setup_card.setObjectName("codexSetupCard")
        setup = QVBoxLayout(self.setup_card)
        self.cli_status_label = QLabel("Codex CLI durumu · Kontrol edilmedi", self.setup_card)
        self.cli_version_label = QLabel("Version · Bilinmiyor", self.setup_card)
        self.auth_status_label = QLabel("Authentication · Bilinmiyor", self.setup_card)
        self.candidate_label = QLabel("Executable · Bilinmiyor", self.setup_card)
        self.privacy_label = QLabel(
            "Codex seçilen workspace içindeki gerekli dosyalara erişebilir ve OpenAI hizmetlerine "
            "veri gönderebilir. Lina credential içeriğini okumaz; yalnız güvenli görev metadata'sı saklar.",
            self.setup_card,
        )
        self.privacy_label.setWordWrap(True)
        self.refresh_button = QPushButton("Durumu Yenile", self.setup_card)
        self.login_button = QPushButton("ChatGPT ile Giriş Yap", self.setup_card)
        self.device_login_button = QPushButton("Device Code ile Giriş", self.setup_card)
        self.logout_button = QPushButton("Oturumu Kapat", self.setup_card)
        self.update_guide_button = QPushButton("Codex'i Güncelle Rehberi", self.setup_card)
        self.diagnostics_button = QPushButton("Ayrıntılar", self.setup_card)
        self.terminal_button = QPushButton("Terminalde Aç", self.setup_card)
        for widget in (
            self.cli_status_label, self.cli_version_label, self.auth_status_label,
            self.candidate_label, self.privacy_label, self.refresh_button, self.login_button,
            self.device_login_button, self.logout_button, self.terminal_button,
            self.diagnostics_button, self.update_guide_button,
        ):
            setup.addWidget(widget)
        self.refresh_button.clicked.connect(self.refresh_requested)
        self.login_button.clicked.connect(self.login_requested)
        self.device_login_button.clicked.connect(self.device_login_requested)
        self.logout_button.clicked.connect(self.logout_requested)
        self.diagnostics_button.clicked.connect(self.diagnostics_requested)
        self.update_guide_button.clicked.connect(self.installation_guide_requested)
        self.terminal_button.clicked.connect(self.terminal_requested)

        self.stop_button = QPushButton("Görevi Durdur", self)
        self.stop_button.clicked.connect(self.stop_requested)

        self.workspace_card = QWidget(self)
        self.workspace_card.setObjectName("codexWorkspaceCard")
        workspace = QVBoxLayout(self.workspace_card)
        self.workspace_summary = QLabel(
            "Codex ile çalışmak için önce çalışma klasörünü seçmelisin.", self.workspace_card
        )
        self.workspace_summary.setWordWrap(True)
        self.workspace_select_button = QPushButton("Klasör Seç", self.workspace_card)
        self.workspace_cancel_button = QPushButton("İptal", self.workspace_card)
        workspace.addWidget(self.workspace_summary)
        workspace.addWidget(self.workspace_select_button)
        workspace.addWidget(self.workspace_cancel_button)
        self.workspace_select_button.clicked.connect(self.workspace_select_requested)
        self.workspace_cancel_button.clicked.connect(self.workspace_cancel_requested)

        self.approval_card = QWidget(self)
        self.approval_card.setObjectName("codexApprovalCard")
        approval = QVBoxLayout(self.approval_card)
        self.approval_summary = QLabel(
            "Bu görev başlamadan önce onayın gerekiyor.", self.approval_card
        )
        self.approval_summary.setWordWrap(True)
        self.approve_button = QPushButton("Onayla", self.approval_card)
        self.deny_button = QPushButton("Reddet", self.approval_card)
        self.edit_button = QPushButton("Düzenle", self.approval_card)
        approval.addWidget(self.approval_summary)
        for button in (self.approve_button, self.deny_button, self.edit_button):
            approval.addWidget(button)
        self.approve_button.clicked.connect(self.approve_requested)
        self.deny_button.clicked.connect(self.deny_requested)
        self.edit_button.clicked.connect(self.edit_requested)

        self.review_card = QWidget(self)
        self.review_card.setObjectName("codexReviewSummaryCard")
        review = QVBoxLayout(self.review_card)
        self.review_summary_label = QLabel("Değişiklik incelemesi beklenmiyor.", self.review_card)
        self.review_summary_label.setWordWrap(True)
        self.review_button = QPushButton("Değişiklikleri İncele", self.review_card)
        self.review_button.clicked.connect(self.review_requested)
        review.addWidget(self.review_summary_label)
        review.addWidget(self.review_button)

        self.recovery_card = QWidget(self)
        self.recovery_card.setObjectName("codexRecoveryCard")
        recovery = QVBoxLayout(self.recovery_card)
        self.recovery_label = QLabel(
            "Önceki Codex görevi tamamlanmadan kapanmış.", self.recovery_card
        )
        self.recovery_label.setWordWrap(True)
        self.recovery_inspect_button = QPushButton("Durumu İncele", self.recovery_card)
        self.recovery_resume_button = QPushButton("Güvenliyse Devam Et", self.recovery_card)
        self.recovery_restart_button = QPushButton("Yeni Görev Olarak Başlat", self.recovery_card)
        self.recovery_remove_button = QPushButton("Geçmişten Kaldır", self.recovery_card)
        for widget in (
            self.recovery_label, self.recovery_inspect_button, self.recovery_resume_button,
            self.recovery_restart_button, self.recovery_remove_button,
        ):
            recovery.addWidget(widget)
        self._recovery_item = None
        self.recovery_inspect_button.clicked.connect(
            lambda: self.recovery_inspect_requested.emit(self._recovery_item))
        self.recovery_resume_button.clicked.connect(self.resume_requested)
        self.recovery_restart_button.clicked.connect(
            lambda: self.recovery_restart_requested.emit(self._recovery_item))
        self.recovery_remove_button.clicked.connect(
            lambda: self.recovery_remove_requested.emit(self._recovery_item))

        self.history_label = QLabel("Geçmiş · Henüz görev yok", self)
        self.history_label.setObjectName("codexHistory")
        self.history_label.setWordWrap(True)
        for widget in (
            self.setup_card, self.task_label, self.status_label, self.workspace_label,
            self.progress, self.stop_button, self.workspace_card, self.approval_card,
            self.review_card, self.recovery_card, self.history_label,
        ):
            layout.addWidget(widget)
        self.render(None)

    def render(
        self,
        session: CodexSession | None,
        history: tuple[CodexHistoryEntry, ...] = (),
        info: CodexCliInfo | None = None,
        change_set: CodexChangeSet | None = None,
        recovery: tuple[CodexHistoryEntry, ...] = (),
    ) -> None:
        self.setVisible(True)
        self.render_cli_info(info)
        if session is None:
            self.task_label.setText("Aktif Codex görevi yok.")
            self.status_label.setText("Durum · Hazır")
            self.workspace_label.setText("Workspace · Seçilmedi")
            self.progress.setValue(0)
            waiting = False
        else:
            self.task_label.setText(f"Aktif görev · {session.task_summary}")
            status_text = {
                "created": "Hazır", "planning": "Görev hazırlanıyor",
                "waiting_approval": "Onay bekliyor", "running": "Çalışıyor",
                "analyzing": "Analiz ediliyor", "verifying": "Doğrulanıyor",
                "completed": "Tamamlandı", "failed": "Başarısız",
                "cancelled": "İptal edildi", "interrupted": "Kesintiye uğradı",
                "paused": "Duraklatıldı",
            }.get(session.status.value, session.status.value)
            self.status_label.setText(f"Durum · {status_text}")
            self.workspace_label.setText(f"Workspace · {session.project_context.root_path.name}")
            self.progress.setValue(session.progress)
            waiting = session.status is CodexSessionStatus.WAITING_APPROVAL
            if session.task is not None:
                targets = ", ".join(
                    action.target for action in session.task.requested_actions if action.target
                )
                self.approval_summary.setText(
                    f"Amaç: {session.task.objective}\nRisk: {session.task.risk_level.value}"
                    + (f"\nDosya: {targets}" if targets else "")
                )
        self.approval_card.setVisible(waiting)
        self.stop_button.setVisible(session is not None and not session.terminal and not waiting)
        self.workspace_card.hide()
        self.review_card.setVisible(bool(change_set and change_set.files))
        if change_set and change_set.files:
            state = "İnceleme bekliyor" if session and session.review_pending else "İncelendi"
            self.review_summary_label.setText(
                f"Codex {change_set.changed_file_count} dosyada değişiklik yaptı.\n"
                f"+{change_set.additions} / -{change_set.deletions} · {state}"
            )
        self._recovery_item = recovery[0] if recovery else None
        self.recovery_card.setVisible(bool(recovery))
        if recovery:
            item = recovery[0]
            self.recovery_label.setText(
                f"Önceki Codex görevi tamamlanmadan kapanmış.\n"
                f"{item.task_summary} · {item.workspace_display_name or 'Workspace'} · {item.status.value}"
            )
            self.recovery_resume_button.setEnabled(item.resumable)
        summaries = [
            f"{item.created_at.date()} · {item.task_summary} · {item.status.value} · "
            f"{item.changed_file_count} dosya"
            for item in history[:5]
        ]
        self.history_label.setText(
            "Geçmiş\n" + "\n".join(summaries) if summaries else "Geçmiş · Henüz görev yok"
        )

    def render_cli_info(self, info: CodexCliInfo | None) -> None:
        if info is None or not info.available:
            self.cli_status_label.setText("Codex CLI durumu · CLI bulunamadı")
            self.cli_version_label.setText("Version · Bilinmiyor")
            self.auth_status_label.setText("Authentication · Kontrol edilemedi")
            self.candidate_label.setText("Executable · Kullanılamıyor")
            self.login_button.hide()
            self.device_login_button.hide()
            self.logout_button.hide()
            self.update_guide_button.show()
            return
        self.cli_version_label.setText(f"Version · {info.version or 'Bilinmiyor'}")
        name = info.executable_path.name if info.executable_path else "Bilinmiyor"
        self.candidate_label.setText(
            f"Executable · {name} · {info.selected_candidate_source} · {info.executable_kind}"
        )
        if info.authenticated and info.ready:
            self.cli_status_label.setText("Codex CLI durumu · Hazır")
            self.auth_status_label.setText(f"Authentication · Bağlı ({info.auth_method_summary})")
        elif info.authenticated:
            self.cli_status_label.setText("Codex CLI durumu · Güncelleme gerekli")
            self.auth_status_label.setText(f"Authentication · Bağlı ({info.auth_method_summary})")
        else:
            self.cli_status_label.setText("Codex CLI durumu · Oturum gerekli")
            self.auth_status_label.setText("Authentication · Oturum gerekli")
        self.login_button.setVisible(not info.authenticated)
        self.device_login_button.setVisible(not info.authenticated and info.supports_device_auth)
        self.logout_button.setVisible(info.authenticated)
        self.update_guide_button.setVisible(not info.ready and info.authenticated)

    def render_workspace_required(self, request: str) -> None:
        self.setVisible(True)
        self.task_label.setText("Codex görevi hazırlanıyor")
        self.status_label.setText("Durum · Workspace bekleniyor")
        self.workspace_label.setText("Workspace · Seçilmedi")
        self.progress.setValue(0)
        self.workspace_summary.setText(
            "Codex ile analiz yapabilmem için önce çalışma klasörünü seçmelisin.\n\n"
            f"İstek: {request[:240]}"
        )
        self.workspace_card.show()
        self.approval_card.hide()
