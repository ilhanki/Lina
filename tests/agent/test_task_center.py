from datetime import datetime, timedelta, timezone

from lina.agent import (
    AgentPlan,
    AgentSession,
    AgentSessionRepository,
    AgentSessionStatus,
    AgentStep,
    AgentStepStatus,
    AgentTaskCenter,
    TaskCenterSection,
)


def _save(repository, status, *, conversation=1, template_id="reminders.summary", age_days=0):
    session = AgentSession.create(conversation, "private user request")
    session.status = status
    session.created_at = datetime.now(timezone.utc) - timedelta(days=age_days)
    session.updated_at = session.created_at
    first = AgentStep("one", "Hatırlatıcıları getir", "Oku", "reminder.list", {})
    second = AgentStep("two", "Sonucu göster", "Göster", "memory.recall", {"query": "private"})
    first.status = AgentStepStatus.SUCCEEDED
    session.plan = AgentPlan("plan", "private plan", [first, second], template_id=template_id, title="private title")
    repository.save(session)
    return session


def test_task_center_sections_status_progress_and_contextual_actions(tmp_path):
    repository = AgentSessionRepository(tmp_path / "agent.json")
    active = _save(repository, AgentSessionStatus.RUNNING)
    waiting = _save(repository, AgentSessionStatus.AWAITING_STEP_APPROVAL, conversation=2)
    paused = _save(repository, AgentSessionStatus.PAUSED, conversation=3)
    interrupted = _save(repository, AgentSessionStatus.INTERRUPTED, conversation=4)
    completed = _save(repository, AgentSessionStatus.COMPLETED, conversation=5)
    failed = _save(repository, AgentSessionStatus.FAILED, conversation=6)
    cancelled = _save(repository, AgentSessionStatus.CANCELLED, conversation=7)
    center = AgentTaskCenter(repository)
    sections = center.sections()
    assert sections[TaskCenterSection.ACTIVE][0].session_id == active.session_id
    assert sections[TaskCenterSection.WAITING_APPROVAL][0].session_id == waiting.session_id
    assert sections[TaskCenterSection.PAUSED][0].session_id == paused.session_id
    assert sections[TaskCenterSection.INTERRUPTED][0].session_id == interrupted.session_id
    assert sections[TaskCenterSection.COMPLETED][0].session_id == completed.session_id
    assert sections[TaskCenterSection.FAILED][0].session_id == failed.session_id
    assert sections[TaskCenterSection.CANCELLED][0].session_id == cancelled.session_id
    summary = center.get(completed.session_id)
    assert summary.progress_current == 1 and summary.progress_total == 2
    assert summary.progress_percent == 50
    assert summary.conversation_id == 5
    assert summary.actions == ("Sonucu görüntüle", "Geçmişten kaldır")


def test_task_center_recovery_notice_and_safe_metadata_only_removal(tmp_path):
    repository = AgentSessionRepository(tmp_path / "agent.json")
    interrupted = _save(repository, AgentSessionStatus.INTERRUPTED)
    completed = _save(repository, AgentSessionStatus.COMPLETED, conversation=2)
    center = AgentTaskCenter(repository)
    notice = center.recovery_notice()
    assert notice.message == "Yarım kalan bir Agent görevin var."
    assert "Güvenli Kopya" in notice.actions
    assert center.remove_history(interrupted.session_id)
    assert center.get(interrupted.session_id) is None
    assert center.get(completed.session_id) is not None
    assert not center.remove_history("missing")


def test_task_center_filters_and_cleanup(tmp_path):
    repository = AgentSessionRepository(tmp_path / "agent.json")
    old = _save(repository, AgentSessionStatus.COMPLETED, age_days=100)
    recent = _save(repository, AgentSessionStatus.COMPLETED, conversation=2)
    center = AgentTaskCenter(repository)
    assert len(center.list(TaskCenterSection.COMPLETED)) == 2
    assert center.cleanup(30) == 1
    assert center.get(old.session_id) is None
    assert center.get(recent.session_id) is not None
