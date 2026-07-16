from lina.agent import AgentPlan, AgentSession, AgentSessionStatus, AgentStep, AgentStepStatus, RiskLevel
from lina.interfaces.qt.agent_panel import AgentPanel


def session(status=AgentSessionStatus.AWAITING_PLAN_APPROVAL):
    value = AgentSession.create(1, "request")
    value.status = status
    value.plan = AgentPlan("p", "Güvenli plan", [
        AgentStep("1", "Hatırlatıcıları listele", "listele", "reminder.list", {}, RiskLevel.READ_ONLY),
        AgentStep("2", "Hatırlatıcı oluştur", "oluştur", "reminder.create", {}, RiskLevel.PERSISTENT, True, dependencies=("1",)),
    ])
    return value


def test_agent_panel_plan_card_and_accessible_statuses(qtbot):
    panel = AgentPanel()
    qtbot.addWidget(panel)
    value = session()
    value.plan.steps[0].status = AgentStepStatus.RUNNING
    panel.render(value, enabled=True)
    assert panel.mode_label.text() == "Agent Mode · Açık"
    assert "1/2" in panel.progress_label.text()
    assert "▶ Çalışıyor" in panel.steps_label.text()
    assert "persistent" in panel.steps_label.text()
    assert panel.start_button.isEnabled()


def test_agent_panel_approval_pause_resume_cancel_controls(qtbot):
    panel = AgentPanel()
    qtbot.addWidget(panel)
    value = session(AgentSessionStatus.AWAITING_STEP_APPROVAL)
    panel.render(value, enabled=True)
    assert panel.approve_button.isEnabled()
    assert panel.skip_button.isEnabled()
    assert panel.cancel_button.isEnabled()
    value.status = AgentSessionStatus.PAUSED
    panel.render(value, enabled=True)
    assert panel.resume_button.isEnabled()
    value.status = AgentSessionStatus.COMPLETED
    panel.render(value, enabled=True)
    assert not panel.cancel_button.isEnabled()
