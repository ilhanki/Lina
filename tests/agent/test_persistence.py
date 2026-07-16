import json

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
    assert "private request with secret" in text  # bounded request summary is intentional metadata
    loaded = repository.load_all()
    assert loaded[0]["status"] == "interrupted"
    assert loaded[0]["plan"]["steps"][0]["tool_name"] == "reminder.list"


def test_repository_tolerates_corruption(tmp_path):
    path = tmp_path / "agent.json"
    path.write_text("not json", encoding="utf-8")
    assert AgentSessionRepository(path).load_all() == ()
