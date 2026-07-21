from datetime import datetime, timedelta, timezone
import json
import threading
import time

import pytest

from lina.agent import (
    AgentController,
    AgentErrorCode,
    AgentExecutor,
    AgentLoopDetector,
    AgentPlan,
    AgentPlanner,
    AgentPolicy,
    AgentSession,
    AgentSessionRepository,
    AgentSessionStatus,
    AgentStep,
    AgentStepStatus,
    AgentVerifier,
    ApprovalDecision,
    RiskLevel,
    idempotency_key,
    recovery_actions,
    user_error_message,
)
from lina.agent.models import AgentEvent, AgentEventType, CancellationToken, ExecutionResult
from lina.agent.reliability import checkpoint_for_step, normalized_operation_hash
from lina.brain.routing.models import IntentType, RequestContext, ToolResult
from lina.brain.routing.registry import SafeToolRegistry, ToolDefinition


def _registry(*, persistent=False, results=None, available=lambda: True, execute=None):
    registry = SafeToolRegistry()
    calls = {"count": 0}
    queued = list(results or [ToolResult(True, "tamam", {"id": 1} if persistent else ("ok",))])

    def run(request, context):
        calls["count"] += 1
        if execute is not None:
            return execute(request, context)
        return queued.pop(0) if queued else ToolResult(True, "tamam", ("ok",))

    registry.register(ToolDefinition(
        "reminder.create" if persistent else "reminder.list",
        IntentType.CREATE_REMINDER if persistent else IntentType.LIST_REMINDERS,
        "test",
        {},
        persistent,
        run,
        available,
    ))
    return registry, calls


def _controller(registry, *, repository=None):
    policy = AgentPolicy()
    tool = registry.names()[0]
    persistent = tool == "reminder.create"
    generated = {
        "summary": "Güvenli plan",
        "steps": [{
            "step_id": "one",
            "title": "Hatırlatıcı oluştur" if persistent else "Hatırlatıcıları listele",
            "tool_name": tool,
            "typed_arguments": {},
            "risk_level": "persistent" if persistent else "read_only",
            "verification_rule": "created_id" if persistent else "typed_success",
        }],
    }
    return AgentController(
        AgentPlanner(policy, lambda _context, _repair: generated),
        AgentExecutor(registry, timeout_seconds=0.02),
        AgentVerifier(),
        policy,
        repository,
    )


def _start(controller):
    session = controller.create_session("Agent modunda güvenli görevi yap", 7, 4)
    controller.plan()
    controller.approve_plan(session.session_id, 4)
    return session


def test_cancel_signal_reaches_inflight_executor_without_waiting_for_controller_lock():
    registry, _calls = _registry()
    controller = _controller(registry)
    session = _start(controller)
    started = threading.Event()

    class BlockingExecutor:
        def available(self, _tool):
            return True

        def execute(self, _step, _context, cancellation):
            started.set()
            assert cancellation._event.wait(timeout=1)
            return ExecutionResult(False, "cancelled", error_code="user_cancelled")

        def shutdown(self):
            return None

    controller.executor = BlockingExecutor()
    runner = threading.Thread(target=controller.run)
    runner.start()
    assert started.wait(timeout=1)
    cancelled = controller.cancel(session.session_id)
    runner.join(timeout=1)
    assert runner.is_alive() is False
    assert cancelled.status is AgentSessionStatus.CANCELLED
    assert cancelled.cancellation_token.cancelled


def test_error_taxonomy_has_safe_turkish_messages_and_contextual_actions():
    assert {item.value for item in AgentErrorCode} == {
        "tool_unavailable", "invalid_arguments", "permission_denied", "approval_required",
        "user_cancelled", "timeout", "transient_failure", "persistent_outcome_uncertain",
        "verification_failed", "verification_uncertain", "dependency_failed", "loop_detected",
        "step_limit_reached", "replan_limit_reached", "stale_result", "interrupted",
        "prohibited", "unsupported_request", "storage_failure", "internal_error",
    }
    assert "otomatik" in user_error_message(AgentErrorCode.PERSISTENT_OUTCOME_UNCERTAIN)
    assert recovery_actions(AgentErrorCode.PERSISTENT_OUTCOME_UNCERTAIN)[0] == "Mevcut Kaydı Kontrol Et"
    assert recovery_actions(AgentErrorCode.PROHIBITED) == ()
    assert "secret" not in user_error_message("unknown-code")


def test_idempotency_hash_is_deterministic_and_contains_no_plaintext():
    step = AgentStep("one", "Hatırlatıcı oluştur", "Oluştur", "reminder.create", {"title": "çok gizli başlık"}, RiskLevel.PERSISTENT, True)
    first = idempotency_key("session", step)
    second = idempotency_key("session", step)
    assert first == second
    assert len(first) == 64
    assert "gizli" not in first
    assert normalized_operation_hash(step) != normalized_operation_hash(
        AgentStep("two", "Hatırlatıcı oluştur", "Oluştur", "reminder.create", {"title": "başka"}, RiskLevel.PERSISTENT, True)
    )


def test_loop_detector_catches_repeated_tool_clarification_and_no_progress_replan():
    detector = AgentLoopDetector(repeat_limit=2)
    step = AgentStep("one", "Listele", "Listele", "reminder.list", {})
    assert not detector.observe_step(step).detected
    assert detector.observe_step(step).detected
    assert not detector.observe_clarification("Saat kaçta hatırlatayım?").detected
    assert detector.observe_clarification("Saat kaçta hatırlatayım?").detected
    assert not detector.observe_replan("same", "none").detected
    assert detector.observe_replan("same", "none").detected


def test_retry_v2_retries_read_only_transient_once():
    registry, calls = _registry(results=[
        ToolResult(False, "geçici", error_code="execution_error", retryable=True),
        ToolResult(True, "tamam", ("ok",)),
    ])
    controller = _controller(registry)
    session = _start(controller)
    result = controller.run(7)
    assert result.status is AgentSessionStatus.COMPLETED
    assert calls["count"] == 2
    assert session.metrics.retry_count == 1
    assert session.plan.steps[0].retry_count == 1
    controller.shutdown()


def test_retry_v2_does_not_retry_schema_cancellation_or_persistent_failure():
    policy = AgentPolicy()
    read_only = AgentStep("r", "Listele", "Listele", "reminder.list", {})
    persistent = AgentStep("p", "Oluştur", "Oluştur", "reminder.create", {}, RiskLevel.PERSISTENT, True)
    assert not policy.can_retry(read_only, 1, "invalid_arguments")
    assert not policy.can_retry(read_only, 1, "timeout", cancelled=True)
    assert not policy.can_retry(persistent, 1, "transient_failure")

    registry, calls = _registry(persistent=True, results=[ToolResult(False, "hata", error_code="execution_error", retryable=True)])
    controller = _controller(registry)
    session = _start(controller)
    assert controller.run().status is AgentSessionStatus.AWAITING_STEP_APPROVAL
    result = controller.approve_step(session.session_id, ApprovalDecision.APPROVE, 4)
    assert result.status is AgentSessionStatus.FAILED
    assert calls["count"] == 1
    controller.shutdown()


def test_persistent_timeout_is_uncertain_and_same_idempotency_key_is_not_replayed():
    def slow(_request, _context):
        time.sleep(0.2)
        return ToolResult(True, "geç tamamlandı", {"id": 1})

    registry, calls = _registry(persistent=True, execute=slow)
    executor = AgentExecutor(registry, timeout_seconds=0.005)
    step = AgentStep("p", "Hatırlatıcı oluştur", "Oluştur", "reminder.create", {}, RiskLevel.PERSISTENT, True)
    step.idempotency_key = idempotency_key("session", step)
    first = executor.execute(step, RequestContext(1), CancellationToken())
    second = executor.execute(step, RequestContext(1), CancellationToken())
    assert first.error_code == "persistent_outcome_uncertain"
    assert second.error_code == "persistent_outcome_uncertain"
    assert calls["count"] == 1
    executor.shutdown()


def test_tool_availability_is_rechecked_immediately_before_execution():
    state = {"available": True}
    registry, calls = _registry(available=lambda: state["available"])
    controller = _controller(registry)
    session = _start(controller)
    state["available"] = False
    result = controller.run(7)
    assert result.status is AgentSessionStatus.BLOCKED
    assert result.plan.steps[0].error_code == "tool_unavailable"
    assert calls["count"] == 0
    assert result.metrics.tool_availability_failure_count == 1
    controller.shutdown()


class _FailingRepository:
    def save(self, _session):
        raise OSError("disk secret")


def test_checkpoint_storage_failure_after_persistent_action_becomes_uncertain():
    registry, calls = _registry(persistent=True)
    controller = _controller(registry, repository=_FailingRepository())
    session = _start(controller)
    controller.run()
    result = controller.approve_step(session.session_id, ApprovalDecision.APPROVE, 4)
    assert result.status is AgentSessionStatus.UNCERTAIN
    assert result.error_code == "persistent_outcome_uncertain"
    assert calls["count"] == 1
    controller.shutdown()


def test_checkpoint_contains_only_safe_metadata():
    step = AgentStep("one", "Gizli dosyayı oku", "secret", "files.read", {"target": "secret.txt"})
    step.status = AgentStepStatus.SUCCEEDED
    step.result_summary = "secret file contents"
    checkpoint = checkpoint_for_step(step)
    assert checkpoint.short_result_summary == "Adım deterministic olarak doğrulandı."
    assert not hasattr(checkpoint, "arguments")


def test_repository_is_multi_session_privacy_safe_and_marks_all_active_states_interrupted(tmp_path):
    path = tmp_path / "history.json"
    repository = AgentSessionRepository(path)
    statuses = (
        AgentSessionStatus.RUNNING,
        AgentSessionStatus.PLANNING,
        AgentSessionStatus.AWAITING_PLAN_APPROVAL,
        AgentSessionStatus.AWAITING_STEP_APPROVAL,
        AgentSessionStatus.PAUSED,
    )
    for index, status in enumerate(statuses):
        session = AgentSession.create(index, f"private secret request {index}")
        session.status = status
        session.plan = AgentPlan("p" + str(index), "private plan secret", [
            AgentStep("s", "private title", "private description", "files.read", {"target": "secret.txt"})
        ])
        session.events.append(AgentEvent.create(session.session_id, AgentEventType.STEP_STARTED, "raw secret event"))
        repository.save(session)
    text = path.read_text(encoding="utf-8")
    assert "private secret request" not in text
    assert "private plan secret" not in text
    assert "secret.txt" not in text
    assert "raw secret event" not in text
    assert len(repository.load_all()) == len(statuses)
    assert all(item["status"] == "interrupted" for item in repository.load_all())


def test_history_cleanup_preserves_active_and_pending_and_unlimited(tmp_path):
    repository = AgentSessionRepository(tmp_path / "history.json")
    old = datetime.now(timezone.utc) - timedelta(days=100)
    completed = AgentSession.create(1, "completed")
    completed.status = AgentSessionStatus.COMPLETED
    completed.updated_at = old
    active = AgentSession.create(2, "active")
    active.status = AgentSessionStatus.RUNNING
    active.updated_at = old
    pending = AgentSession.create(3, "pending")
    pending.status = AgentSessionStatus.AWAITING_STEP_APPROVAL
    pending.updated_at = old
    for session in (completed, active, pending):
        repository.save(session)
    assert repository.cleanup(None) == 0
    assert repository.cleanup(30) == 1
    remaining = {item["session_id"] for item in repository.load_all()}
    assert remaining == {active.session_id, pending.session_id}
    with pytest.raises(ValueError):
        repository.cleanup(14)


def test_safe_restart_creates_new_ids_discards_old_approval_and_requires_duplicate_check():
    registry, _calls = _registry(persistent=True)
    controller = _controller(registry)
    session = _start(controller)
    controller.run()
    old_plan_id = session.plan.plan_id
    old_step_id = session.plan.steps[0].step_id
    session.plan.steps[0].status = AgentStepStatus.SUCCEEDED
    session.status = AgentSessionStatus.INTERRUPTED
    restarted = controller.safe_restart(session.session_id)
    assert restarted.session_id != session.session_id
    assert restarted.plan.plan_id != old_plan_id
    assert restarted.plan.steps[0].step_id != old_step_id
    assert restarted.generation_id != session.generation_id
    assert restarted.approval_state is None
    assert restarted.plan.steps[0].status is AgentStepStatus.PENDING
    assert restarted.plan.steps[0].approval_required
    assert restarted.duplicate_check_required
    assert restarted.source_session_id == session.session_id
    controller.shutdown()


def test_shutdown_checkpoints_active_session_as_interrupted_without_auto_resume(tmp_path):
    registry, _calls = _registry()
    repository = AgentSessionRepository(tmp_path / "history.json")
    controller = _controller(registry, repository=repository)
    session = _start(controller)
    controller.shutdown()
    assert session.status is AgentSessionStatus.INTERRUPTED
    loaded = repository.load_all()
    assert loaded[0]["status"] == "interrupted"
    assert loaded[0]["error_code"] == "interrupted"
