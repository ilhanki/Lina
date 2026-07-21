
from lina.agent import AgentPlan, AgentSession, AgentSessionRepository, AgentSessionStatus, AgentStep, RiskLevel


def test_repository_saves_only_safe_metadata_and_marks_restart_interrupted(tmp_path):
    path = tmp_path / "agent.json"
    repository = AgentSessionRepository(path)
    session = AgentSession.create(1, "private request with secret")
    session.status = AgentSessionStatus.RUNNING
    session.plan = AgentPlan("p", "summary", [AgentStep("s", "title", "description", "reminder.list", {"raw": "must-not-persist"}, RiskLevel.READ_ONLY)])
    repository.save(session)
    text = path.read_text(encoding="utf-8")
    assert "must-not-persist" not in text
    assert "typed_arguments" not in text
    assert "private request with secret" not in text
    assert "Agent request (27 characters)" in text
    loaded = repository.load_all()
    assert loaded[0]["status"] == "interrupted"
    assert loaded[0]["plan"]["steps"][0]["tool_name"] == "reminder.list"


def test_repository_tolerates_corruption(tmp_path):
    path = tmp_path / "agent.json"
    path.write_text("not json", encoding="utf-8")
    assert AgentSessionRepository(path).load_all() == ()


def test_restart_recovery_is_persisted_once_without_resuming_execution(tmp_path):
    path = tmp_path / "agent.json"
    repository = AgentSessionRepository(path)
    session = AgentSession.create(1, "private request")
    session.status = AgentSessionStatus.AWAITING_STEP_APPROVAL
    repository.save(session)

    assert repository.recover_interrupted() == 1
    assert repository.recover_interrupted() == 0
    recovered = repository.load_all(recover_interrupted=False)
    assert recovered[0]["status"] == "interrupted"
    assert recovered[0]["error_code"] == "interrupted"
