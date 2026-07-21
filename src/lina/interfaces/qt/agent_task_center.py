"""Accessible task-template, plan-review and Task Center V2 surfaces."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QDate, QTime, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTabWidget,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from lina.agent.models import AgentPlan, AgentSession, RiskLevel
from lina.agent.task_center import AgentTaskCenter, AgentTaskSummary, TaskCenterSection
from lina.agent.templates.models import TaskTemplate, TaskTemplateCategory
from lina.agent.templates.registry import TaskTemplateRegistry


_SECTION_LABELS = {
    TaskCenterSection.ACTIVE: "Aktif",
    TaskCenterSection.WAITING_APPROVAL: "Onay bekleyen",
    TaskCenterSection.PAUSED: "Duraklatılmış",
    TaskCenterSection.INTERRUPTED: "Yarım kalan",
    TaskCenterSection.COMPLETED: "Tamamlanan",
    TaskCenterSection.FAILED: "Başarısız",
    TaskCenterSection.CANCELLED: "İptal edilen",
}
_STATUS_LABELS = {
    "idle": "Hazırlanıyor",
    "planning": "Planlanıyor",
    "awaiting_input": "Bilgi bekliyor",
    "awaiting_plan_approval": "Plan onayı bekliyor",
    "ready": "Başlamaya hazır",
    "running": "Çalışıyor",
    "paused": "Duraklatıldı",
    "awaiting_step_approval": "Adım onayı bekliyor",
    "replanning": "Plan güncelleniyor",
    "completed": "Tamamlandı",
    "partially_completed": "Kısmen tamamlandı",
    "failed": "Başarısız",
    "cancelled": "İptal edildi",
    "blocked": "Engellendi",
    "interrupted": "Yarım kaldı",
    "uncertain": "Sonuç belirsiz",
}


class TaskTemplateBrowserDialog(QDialog):
    template_selected = Signal(str)

    def __init__(self, registry: TaskTemplateRegistry, available_capabilities: set[str], parent=None) -> None:
        super().__init__(parent)
        self.registry = registry
        self.available_capabilities = set(available_capabilities)
        self.setObjectName("taskTemplateBrowser")
        self.setWindowTitle("Hazır Görevler")
        self.setMinimumSize(620, 500)
        layout = QVBoxLayout(self)
        title = QLabel("Hazır Agent Görevleri", self)
        title.setObjectName("settingsPageTitle")
        layout.addWidget(title)
        description = QLabel("Yalnız şu anda kullanılabilir güvenli araçlarla desteklenen görevler gösterilir.", self)
        description.setWordWrap(True)
        layout.addWidget(description)
        self.category = QComboBox(self)
        self.category.setAccessibleName("Görev kategorisi")
        self.category.addItem("Tümü", None)
        for value, label in (
            (TaskTemplateCategory.REMINDERS, "Hatırlatıcılar"),
            (TaskTemplateCategory.MEMORY, "Hafıza"),
            (TaskTemplateCategory.CONVERSATION, "Sohbet"),
            (TaskTemplateCategory.FILES_READ_ONLY, "Dosyalar"),
            (TaskTemplateCategory.VISION, "Vision"),
            (TaskTemplateCategory.SYSTEM_STATUS, "Sistem"),
        ):
            self.category.addItem(label, value.value)
        layout.addWidget(self.category)
        self.items = QListWidget(self)
        self.items.setAccessibleName("Hazır görevler")
        layout.addWidget(self.items, 1)
        self.details = QLabel("Bir görev seç.", self)
        self.details.setWordWrap(True)
        self.details.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.details)
        actions = QHBoxLayout()
        actions.addStretch(1)
        self.use_button = QPushButton("Kullan", self)
        self.use_button.setObjectName("accentButton")
        self.use_button.setAccessibleName("Seçili görev şablonunu kullan")
        self.use_button.setEnabled(False)
        actions.addWidget(self.use_button)
        close = QPushButton("Kapat", self)
        close.clicked.connect(self.reject)
        actions.addWidget(close)
        layout.addLayout(actions)
        self.category.currentIndexChanged.connect(self.reload)
        self.items.currentItemChanged.connect(self._show_current)
        self.items.itemActivated.connect(lambda _item: self._use_current())
        self.use_button.clicked.connect(self._use_current)
        self.reload()

    def reload(self, *_args) -> None:
        self.items.clear()
        category = self.category.currentData()
        templates = self.registry.list(
            category=category,
            available_capabilities=self.available_capabilities,
        )
        for template in templates:
            item = QListWidgetItem(template.title)
            item.setData(Qt.ItemDataRole.UserRole, template.template_id)
            item.setToolTip(template.description)
            self.items.addItem(item)
        if self.items.count():
            self.items.setCurrentRow(0)
        else:
            self.details.setText("Bu kategoride kullanılabilir hazır görev yok.")
            self.use_button.setEnabled(False)

    def _show_current(self, current: QListWidgetItem | None, _previous=None) -> None:
        template = self._template(current)
        self.use_button.setEnabled(template is not None)
        if template is None:
            return
        self.details.setText(
            f"{template.description}\n\nÖrnek: {template.example_phrases[0]}\nRisk: {template.risk_summary}"
        )

    def _template(self, item: QListWidgetItem | None) -> TaskTemplate | None:
        return self.registry.get(str(item.data(Qt.ItemDataRole.UserRole))) if item is not None else None

    def _use_current(self) -> None:
        template = self._template(self.items.currentItem())
        if template is None:
            return
        self.template_selected.emit(template.template_id)
        self.accept()


class TaskTemplateParameterDialog(QDialog):
    """Typed mini form. Accepting it returns data; it never executes a tool."""

    def __init__(self, template: TaskTemplate, parent=None) -> None:
        super().__init__(parent)
        self.template = template
        self.setObjectName("taskTemplateParameters")
        self.setWindowTitle(template.title)
        layout = QVBoxLayout(self)
        description = QLabel(template.description, self)
        description.setWordWrap(True)
        layout.addWidget(description)
        self.form = QFormLayout()
        layout.addLayout(self.form)
        self.fields: dict[str, QWidget] = {}
        for name in template.input_schema:
            field = self._field(name)
            self.fields[name] = field
            self.form.addRow(_field_label(name), field)
        risk = QLabel(f"Risk: {template.risk_summary}", self)
        risk.setWordWrap(True)
        risk.setObjectName("settingsDescription")
        layout.addWidget(risk)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok, self)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Planı Hazırla")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _field(self, name: str) -> QWidget:
        if name == "due_at":
            container = QWidget(self)
            row = QHBoxLayout(container)
            row.setContentsMargins(0, 0, 0, 0)
            date = QDateEdit(QDate.currentDate().addDays(1), container)
            date.setCalendarPopup(True)
            date.setAccessibleName("Hatırlatıcı tarihi")
            clock = QTimeEdit(QTime(10, 0), container)
            clock.setAccessibleName("Hatırlatıcı saati")
            row.addWidget(date)
            row.addWidget(clock)
            container.date_field = date  # type: ignore[attr-defined]
            container.time_field = clock  # type: ignore[attr-defined]
            return container
        if name in {"recurrence", "category", "summary_length", "range"}:
            combo = QComboBox(self)
            choices = {
                "recurrence": (("Tekrarlama yok", "none"), ("Her gün", "daily"), ("Her hafta", "weekly")),
                "category": (("Sohbet tercihi", "conversation_note"),),
                "summary_length": (("Kısa", "short"), ("Orta", "medium")),
                "range": (("Yaklaşanlar", "upcoming"), ("Yarın", "tomorrow"), ("Bu hafta", "week")),
            }[name]
            for label, value in choices:
                combo.addItem(label, value)
            combo.setAccessibleName(_field_label(name))
            return combo
        field = QLineEdit(self)
        field.setAccessibleName(_field_label(name))
        return field

    def parameters(self) -> dict[str, object]:
        values: dict[str, object] = {}
        for name, field in self.fields.items():
            if name == "due_at":
                date = field.date_field.date().toPython()  # type: ignore[attr-defined]
                clock = field.time_field.time().toPython()  # type: ignore[attr-defined]
                values[name] = datetime.combine(date, clock).astimezone()
            elif isinstance(field, QComboBox):
                values[name] = field.currentData()
            elif isinstance(field, QLineEdit):
                values[name] = field.text().strip()
        return values


class AgentStepArgumentsDialog(QDialog):
    """Edit a pending step through its real tool schema; never executes the tool."""

    def __init__(self, title: str, schema: dict[str, type | tuple[type, ...]], values: dict[str, object], parent=None) -> None:
        super().__init__(parent)
        self.schema = dict(schema)
        self.setObjectName("agentStepArguments")
        self.setWindowTitle(f"{title} · Girdileri Düzenle")
        layout = QVBoxLayout(self)
        explanation = QLabel("Değişiklik yeni bir plan revision’ı oluşturur ve yeniden onaylanır.", self)
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        self.form = QFormLayout()
        layout.addLayout(self.form)
        self.fields: dict[str, QWidget] = {}
        for name, kind in self.schema.items():
            field = self._field(name, kind, values.get(name))
            self.fields[name] = field
            self.form.addRow(_field_label(name), field)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok, self)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Planı Güncelle")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _field(self, name: str, kind: type | tuple[type, ...], current: object) -> QWidget:
        kinds = kind if isinstance(kind, tuple) else (kind,)
        if datetime in kinds:
            value = current if isinstance(current, datetime) else datetime.now().astimezone()
            container = QWidget(self)
            row = QHBoxLayout(container)
            row.setContentsMargins(0, 0, 0, 0)
            date = QDateEdit(QDate(value.year, value.month, value.day), container)
            date.setCalendarPopup(True)
            clock = QTimeEdit(QTime(value.hour, value.minute), container)
            date.setAccessibleName(f"{_field_label(name)} tarihi")
            clock.setAccessibleName(f"{_field_label(name)} saati")
            row.addWidget(date)
            row.addWidget(clock)
            container.date_field = date  # type: ignore[attr-defined]
            container.time_field = clock  # type: ignore[attr-defined]
            return container
        if name in {"recurrence", "range", "summary_length", "category"}:
            combo = QComboBox(self)
            choices = {
                "recurrence": (("Tekrarlama yok", "none"), ("Her gün", "daily"), ("Her hafta", "weekly")),
                "range": (("Yaklaşanlar", "upcoming"), ("Yarın", "tomorrow"), ("Bu hafta", "week")),
                "summary_length": (("Kısa", "short"), ("Orta", "medium")),
                "category": (("Sohbet tercihi", "conversation_note"),),
            }[name]
            for label, value in choices:
                combo.addItem(label, value)
            resolved = getattr(current, "value", current)
            index = combo.findData(resolved)
            combo.setCurrentIndex(max(index, 0))
            combo.setAccessibleName(_field_label(name))
            return combo
        field = QLineEdit(str(current or ""), self)
        field.setAccessibleName(_field_label(name))
        return field

    def arguments(self) -> dict[str, object]:
        values: dict[str, object] = {}
        for name, field in self.fields.items():
            if hasattr(field, "date_field"):
                date = field.date_field.date().toPython()  # type: ignore[attr-defined]
                clock = field.time_field.time().toPython()  # type: ignore[attr-defined]
                values[name] = datetime.combine(date, clock).astimezone()
            elif isinstance(field, QComboBox):
                values[name] = field.currentData()
            else:
                values[name] = field.text().strip()  # type: ignore[union-attr]
        return values


class PlanReviewWidget(QWidget):
    start_requested = Signal()
    skip_requested = Signal(str)
    remove_requested = Signal(str)
    move_requested = Signal(str, int)
    arguments_requested = Signal(str)
    regenerate_requested = Signal()
    cancel_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("agentPlanReview")
        self.setAccessibleName("Agent plan inceleme")
        layout = QVBoxLayout(self)
        self.summary = QLabel("Plan hazırlanıyor…", self)
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.steps = QListWidget(self)
        self.steps.setAccessibleName("Agent plan adımları")
        layout.addWidget(self.steps, 1)
        self.details = QLabel("Bir adım seç.", self)
        self.details.setWordWrap(True)
        layout.addWidget(self.details)
        actions = QHBoxLayout()
        self.up_button = _button("Yukarı", actions, lambda: self._move(-1), self)
        self.down_button = _button("Aşağı", actions, lambda: self._move(1), self)
        self.skip_button = _button("Atla", actions, self._skip, self)
        self.remove_button = _button("Opsiyoneli Kaldır", actions, self._remove, self)
        self.arguments_button = _button("Girdileri Düzenle", actions, self._arguments, self)
        self.regenerate_button = _button("Yeniden Üret", actions, self.regenerate_requested.emit, self)
        self.cancel_button = _button("İptal", actions, self.cancel_requested.emit, self)
        self.start_button = _button("Başlat", actions, self.start_requested.emit, self)
        self.start_button.setObjectName("accentButton")
        layout.addLayout(actions)
        self.steps.currentItemChanged.connect(self._show_step)
        self._plan: AgentPlan | None = None

    def render(self, plan: AgentPlan | None) -> None:
        self._plan = plan
        self.steps.clear()
        if plan is None:
            self.summary.setText("Plan henüz hazırlanmadı.")
            return
        persistent = any(step.risk_level in {RiskLevel.PERSISTENT, RiskLevel.SENSITIVE} for step in plan.steps)
        self.summary.setText(
            f"{plan.summary}\n{len(plan.steps)} adım · Kalıcı işlem: {'Var; ayrı onay gerekir' if persistent else 'Yok'}"
        )
        for index, step in enumerate(plan.steps, 1):
            item = QListWidgetItem(f"{index}. {step.title} · {_risk_label(step.risk_level)}")
            item.setData(Qt.ItemDataRole.UserRole, step.step_id)
            self.steps.addItem(item)
        if self.steps.count():
            self.steps.setCurrentRow(0)

    def _current_step(self):
        item = self.steps.currentItem()
        step_id = str(item.data(Qt.ItemDataRole.UserRole)) if item is not None else ""
        return next((step for step in self._plan.steps if step.step_id == step_id), None) if self._plan else None

    def _show_step(self, *_args) -> None:
        step = self._current_step()
        if step is None:
            return
        dependencies = ", ".join(step.dependencies) if step.dependencies else "Yok"
        approval = "Gerekli" if step.approval_required or step.risk_level in {RiskLevel.PERSISTENT, RiskLevel.SENSITIVE} else "Gerekli değil"
        self.details.setText(
            f"{step.description}\nAraç: {step.tool_name}\nRisk: {_risk_label(step.risk_level)}\nOnay: {approval}\nBağımlılıklar: {dependencies}"
        )
        self.remove_button.setEnabled(step.optional)
        self.arguments_button.setEnabled(bool(step.typed_arguments) and step.status.value == "pending")

    def _move(self, direction: int) -> None:
        step = self._current_step()
        if step is not None:
            self.move_requested.emit(step.step_id, direction)

    def _skip(self) -> None:
        step = self._current_step()
        if step is not None:
            self.skip_requested.emit(step.step_id)

    def _remove(self) -> None:
        step = self._current_step()
        if step is not None and step.optional:
            self.remove_requested.emit(step.step_id)

    def _arguments(self) -> None:
        step = self._current_step()
        if step is not None and self.arguments_button.isEnabled():
            self.arguments_requested.emit(step.step_id)


class AgentInspectorV2(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("agentInspectorV2")
        self.setAccessibleName("Agent görev ayrıntıları")
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget(self)
        self.tabs.setAccessibleName("Agent görev ayrıntısı bölümleri")
        self.summary = self._page("Aktif görev yok.")
        self.plan = self._page("Plan yok.")
        self.history = self._page("Görev geçmişi yok.")
        self.technical = self._page("Teknik durum yok.")
        for label, page in (("Özet", self.summary), ("Plan", self.plan), ("Geçmiş", self.history), ("Teknik Durum", self.technical)):
            self.tabs.addTab(page.parentWidget(), label)
        layout.addWidget(self.tabs)

    def _page(self, text: str) -> QLabel:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        label = QLabel(text, page)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(label)
        layout.addStretch(1)
        return label

    def render(self, session: AgentSession | None) -> None:
        if session is None:
            self.summary.setText("Aktif görev yok.")
            return
        plan = session.plan
        total = len(plan.steps) if plan else 0
        current = min(session.current_step_index, total)
        self.summary.setText(
            f"Amaç: {plan.title if plan else 'Plan hazırlanıyor'}\n"
            f"Durum: {_STATUS_LABELS.get(session.status.value, session.status.value)}\n"
            f"İlerleme: {current}/{total}\n"
            f"Şablon: {plan.template_id if plan and plan.template_id else 'Genel plan'}\n"
            f"Başlangıç: {session.created_at.astimezone().strftime('%d.%m.%Y %H:%M')}\n"
            f"Son işlem: {session.last_summary or 'Görev oluşturuldu.'}"
        )
        self.plan.setText("\n\n".join(
            f"{index}. {step.title}\nRisk: {_risk_label(step.risk_level)} · Doğrulama: {step.verification_rule.kind} · Onay: {'Gerekli' if step.approval_required else 'Gerekli değil'}"
            for index, step in enumerate(plan.steps, 1)
        ) if plan else "Plan hazırlanıyor…")
        visible_events = [event for event in session.events if event.user_visible]
        self.history.setText("\n".join(
            f"{event.timestamp.astimezone().strftime('%H:%M')} · {event.short_summary}"
            for event in visible_events[-20:]
        ) or "Henüz görev olayı yok.")
        self.technical.setText(
            f"Oturum: {session.session_id[:8]}…\n"
            f"Hata kodu: {session.error_code or 'Yok'}\n"
            f"Retry: {session.metrics.retry_count}\n"
            f"Replan: {session.metrics.replan_count}\n"
            f"Belirsiz sonuç: {session.metrics.uncertain_outcome_count}"
        )
        self.tabs.setCurrentIndex(0)


class AgentTaskCenterDialog(QDialog):
    open_requested = Signal(str)
    restart_requested = Signal(str)

    def __init__(self, center: AgentTaskCenter, parent=None) -> None:
        super().__init__(parent)
        self.center = center
        self.setObjectName("agentTaskCenter")
        self.setWindowTitle("Agent Görev Merkezi")
        self.setMinimumSize(760, 560)
        layout = QVBoxLayout(self)
        title = QLabel("Agent Görev Merkezi", self)
        title.setObjectName("settingsPageTitle")
        layout.addWidget(title)
        self.tabs = QTabWidget(self)
        self.tabs.setAccessibleName("Agent görev durumları")
        self.lists: dict[TaskCenterSection, QListWidget] = {}
        for section in TaskCenterSection:
            page = QWidget(self)
            page_layout = QVBoxLayout(page)
            items = QListWidget(page)
            items.setAccessibleName(f"{_SECTION_LABELS[section]} Agent görevleri")
            items.itemActivated.connect(lambda _item, s=section: self._open(s))
            page_layout.addWidget(items)
            self.tabs.addTab(page, _SECTION_LABELS[section])
            self.lists[section] = items
        layout.addWidget(self.tabs, 1)
        self.details = QLabel("Bir görev seç.", self)
        self.details.setWordWrap(True)
        layout.addWidget(self.details)
        actions = QHBoxLayout()
        self.open_button = _button("Aç", actions, self._open_current, self)
        self.restart_button = _button("Güvenli Kopya", actions, self._restart_current, self)
        self.remove_button = _button("Geçmişten Kaldır", actions, self._remove_current, self)
        _button("Kapat", actions, self.accept, self)
        layout.addLayout(actions)
        for items in self.lists.values():
            items.currentItemChanged.connect(self._show_current)
        self.tabs.currentChanged.connect(lambda _index: self._show_current())
        self.reload()

    def reload(self) -> None:
        sections = self.center.sections()
        for section, widget in self.lists.items():
            widget.clear()
            for task in sections[section]:
                item = QListWidgetItem(
                    f"{task.title} · {_STATUS_LABELS.get(task.status, task.status)} · {task.progress_percent}%"
                )
                item.setData(Qt.ItemDataRole.UserRole, task.session_id)
                item.setToolTip(task.last_summary)
                widget.addItem(item)
            if not sections[section]:
                empty = QListWidgetItem("Bu bölümde görev yok.")
                empty.setFlags(empty.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                widget.addItem(empty)
        self._show_current()

    def _current(self) -> AgentTaskSummary | None:
        section = list(TaskCenterSection)[self.tabs.currentIndex()]
        item = self.lists[section].currentItem()
        session_id = str(item.data(Qt.ItemDataRole.UserRole)) if item is not None and item.data(Qt.ItemDataRole.UserRole) else ""
        return self.center.get(session_id) if session_id else None

    def _show_current(self, *_args) -> None:
        task = self._current()
        if task is None:
            self.details.setText("Bir görev seç.")
            self.open_button.setEnabled(False)
            self.restart_button.setEnabled(False)
            self.remove_button.setEnabled(False)
            return
        started = task.started_at.astimezone().strftime("%d.%m.%Y %H:%M") if task.started_at else "Bilinmiyor"
        self.details.setText(
            f"{task.last_summary}\nBaşlangıç: {started}\nSohbet: {task.conversation_id if task.conversation_id is not None else 'Silinmiş'}"
        )
        self.open_button.setEnabled(True)
        self.restart_button.setEnabled("Güvenli kopya olarak yeniden başlat" in task.actions)
        self.remove_button.setEnabled("Geçmişten kaldır" in task.actions or "Geçmişte bırak" in task.actions)

    def _open(self, _section=None) -> None:
        self._open_current()

    def _open_current(self) -> None:
        task = self._current()
        if task is not None:
            self.open_requested.emit(task.session_id)

    def _restart_current(self) -> None:
        task = self._current()
        if task is not None and self.restart_button.isEnabled():
            self.restart_requested.emit(task.session_id)

    def _remove_current(self) -> None:
        task = self._current()
        if task is not None and self.remove_button.isEnabled():
            self.center.remove_history(task.session_id)
            self.reload()


def _field_label(name: str) -> str:
    return {
        "title": "Başlık",
        "due_at": "Tarih ve saat",
        "recurrence": "Tekrar",
        "content": "Hatırlanacak bilgi",
        "category": "Kategori",
        "query": "Arama",
        "target": "Dosya",
        "summary_length": "Özet uzunluğu",
        "range": "Tarih aralığı",
    }.get(name, name)


def _risk_label(risk: RiskLevel) -> str:
    return {
        RiskLevel.READ_ONLY: "Salt okunur",
        RiskLevel.LOW: "Düşük",
        RiskLevel.PERSISTENT: "Kalıcı",
        RiskLevel.SENSITIVE: "Hassas",
        RiskLevel.PROHIBITED: "Yasak",
    }[risk]


def _button(text: str, layout: QHBoxLayout, callback, parent: QWidget) -> QPushButton:
    button = QPushButton(text, parent)
    button.setAccessibleName(text)
    button.clicked.connect(callback)
    layout.addWidget(button)
    return button
