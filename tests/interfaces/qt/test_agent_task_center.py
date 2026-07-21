from datetime import datetime

from PySide6.QtCore import Qt

from lina.agent import (
    AgentEvent,
    AgentEventType,
    AgentPlan,
    AgentSession,
    AgentSessionRepository,
    AgentSessionStatus,
    AgentStep,
    AgentTaskCenter,
    RiskLevel,
    TaskCenterSection,
)
from lina.agent.templates import build_builtin_template_registry
from lina.interfaces.qt.agent_task_center import (
    AgentInspectorV2,
    AgentStepArgumentsDialog,
    AgentTaskCenterDialog,
    PlanReviewWidget,
    TaskTemplateBrowserDialog,
    TaskTemplateParameterDialog,
)


def _session(status=AgentSessionStatus.AWAITING_PLAN_APPROVAL):
    session = AgentSession.create(4, "private raw request")
    session.status = status
    session.plan = AgentPlan("plan", "Güvenli plan", [
        AgentStep("one", "Hatırlatıcıları getir", "Kayıtları oku", "reminder.list", {}),
        AgentStep("two", "Hatırlatıcıyı oluştur", "Kalıcı kaydı oluştur", "reminder.create", {"title": "private"}, RiskLevel.PERSISTENT, True, dependencies=("one",), optional=True),
    ], template_id="reminders.create", title="Hatırlatıcı oluştur")
    session.events.append(AgentEvent.create(session.session_id, AgentEventType.PLAN_CREATED, "Plan oluşturuldu."))
    return session


def test_template_browser_filters_real_capabilities_and_emits_selection(qtbot):
    dialog = TaskTemplateBrowserDialog(
        build_builtin_template_registry(), {"reminder.summary", "reminder.conflicts"}
    )
    qtbot.addWidget(dialog)
    assert dialog.items.count() == 2
    assert "Hatırlatıcı" in dialog.items.item(0).text()
    assert dialog.use_button.accessibleName()
    with qtbot.waitSignal(dialog.template_selected) as signal:
        qtbot.mouseClick(dialog.use_button, Qt.MouseButton.LeftButton)
    assert signal.args[0] in {"reminders.summary", "reminders.conflicts"}


def test_template_parameter_form_returns_typed_data_without_execution(qtbot):
    template = build_builtin_template_registry().require("reminders.create")
    dialog = TaskTemplateParameterDialog(template)
    qtbot.addWidget(dialog)
    dialog.fields["title"].setText("Agent testi")
    values = dialog.parameters()
    assert values["title"] == "Agent testi"
    assert isinstance(values["due_at"], datetime)
    assert values["recurrence"] == "none"


def test_step_arguments_dialog_preserves_typed_values_without_execution(qtbot):
    due_at = datetime.now().astimezone()
    dialog = AgentStepArgumentsDialog(
        "Hatırlatıcıyı oluştur",
        {"title": str, "due_at": datetime, "recurrence": str},
        {"title": "İlk başlık", "due_at": due_at, "recurrence": "weekly"},
    )
    qtbot.addWidget(dialog)
    assert dialog.fields["title"].text() == "İlk başlık"
    assert dialog.fields["recurrence"].currentData() == "weekly"
    values = dialog.arguments()
    assert isinstance(values["due_at"], datetime)
    assert values["recurrence"] == "weekly"


def test_plan_review_shows_tool_risk_approval_dependencies_and_edit_signals(qtbot):
    widget = PlanReviewWidget()
    qtbot.addWidget(widget)
    session = _session()
    widget.render(session.plan)
    assert widget.steps.count() == 2
    widget.steps.setCurrentRow(1)
    assert "İşlem: Hatırlatıcı oluşturma" in widget.details.text()
    assert "Kalıcı" in widget.details.text()
    assert "Gerekli" in widget.details.text()
    assert "Hatırlatıcıları getir" in widget.details.text()
    assert widget.remove_button.isEnabled()
    assert widget.arguments_button.isEnabled()
    with qtbot.waitSignal(widget.arguments_requested) as arguments_signal:
        qtbot.mouseClick(widget.arguments_button, Qt.MouseButton.LeftButton)
    assert arguments_signal.args == ["two"]
    with qtbot.waitSignal(widget.skip_requested) as signal:
        qtbot.mouseClick(widget.skip_button, Qt.MouseButton.LeftButton)
    assert signal.args == ["two"]


def test_inspector_v2_has_four_sections_short_id_and_no_raw_arguments(qtbot):
    widget = AgentInspectorV2()
    qtbot.addWidget(widget)
    session = _session()
    session.metrics.retry_count = 1
    widget.render(session)
    assert [widget.tabs.tabText(index) for index in range(widget.tabs.count())] == ["Özet", "Plan", "Geçmiş", "Teknik Durum"]
    assert session.session_id[:8] in widget.technical.text()
    assert session.session_id not in widget.technical.text()
    assert "private raw request" not in widget.summary.text()
    assert "private" not in widget.plan.text()
    assert widget.tabs.currentIndex() == 0


def test_task_center_dialog_sections_recovery_restart_and_history_removal(qtbot, tmp_path):
    repository = AgentSessionRepository(tmp_path / "agent.json")
    interrupted = _session(AgentSessionStatus.INTERRUPTED)
    failed = _session(AgentSessionStatus.FAILED)
    failed.conversation_id = 8
    repository.save(interrupted)
    repository.save(failed)
    dialog = AgentTaskCenterDialog(AgentTaskCenter(repository))
    qtbot.addWidget(dialog)
    assert dialog.tabs.count() == 7
    interrupted_index = list(TaskCenterSection).index(TaskCenterSection.INTERRUPTED)
    dialog.tabs.setCurrentIndex(interrupted_index)
    dialog.lists[TaskCenterSection.INTERRUPTED].setCurrentRow(0)
    assert dialog.restart_button.isEnabled()
    with qtbot.waitSignal(dialog.restart_requested) as signal:
        qtbot.mouseClick(dialog.restart_button, Qt.MouseButton.LeftButton)
    assert signal.args == [interrupted.session_id]
    qtbot.mouseClick(dialog.remove_button, Qt.MouseButton.LeftButton)
    assert dialog.center.get(interrupted.session_id) is None
    assert dialog.center.get(failed.session_id) is not None
