from __future__ import annotations

from datetime import datetime

import pytest

from lina.agent import (
    AgentContext, AgentController, AgentExecutor, AgentPlan, AgentPlanner, AgentPolicy,
    AgentSessionStatus, AgentStep, AgentStepStatus, AgentVerifier, ApprovalDecision,
    CapabilitySnapshot, ExecutionResult, RiskLevel, VerificationRule, VerificationStatus,
    parse_approval,
)
from lina.agent.errors import AgentPlanError, AgentPolicyError, AgentStateError
from lina.brain.routing.models import IntentType, ToolResult
from lina.brain.routing.registry import SafeToolRegistry, ToolDefinition


class Registry(SafeToolRegistry):
    def __init__(self, *, fail=False, data=("ok",), persistent=False):
        super().__init__()
        self.calls = 0
        self.fail = fail
        self.data = data

        def execute(_request, _context):
            self.calls += 1
            return ToolResult(not self.fail, "sonuç", self.data if not self.fail else None, "failed" if self.fail else None)

        self.register(ToolDefinition(
            "reminder.create" if persistent else "reminder.list",
            IntentType.CREATE_REMINDER if persistent else IntentType.LIST_REMINDERS,
            "test tool", {}, persistent, execute,
        ))


def capability(name="reminder.list", risk=RiskLevel.READ_ONLY):
    return CapabilitySnapshot(name, "test", (), "ToolResult", risk, risk is RiskLevel.PERSISTENT, True, risk is RiskLevel.READ_ONLY)


def step(step_id="one", *, tool="reminder.list", risk=RiskLevel.READ_ONLY, dependencies=(), rule="typed_success"):
    return AgentStep(step_id, "Başlık", "Açıklama", tool, {}, risk, risk is RiskLevel.PERSISTENT, dependencies=dependencies, verification_rule=rule)


def plan(*steps):
    return AgentPlan("plan", "Özet", list(steps or (step(),)))


@pytest.mark.parametrize("bad_steps", [
    [step("x"), step("x")],
    [step("x", dependencies=("missing",))],
    [step("x", dependencies=("y",)), step("y", dependencies=("x",))],
])
def test_plan_rejects_invalid_graphs(bad_steps):
    with pytest.raises(AgentPlanError):
        plan(*bad_steps)


def test_plan_rejects_hard_step_limit():
    with pytest.raises(AgentPlanError):
        plan(*(step(str(index)) for index in range(13)))


def test_policy_blocks_prohibited_and_unknown_tools():
    policy = AgentPolicy()
    with pytest.raises(AgentPolicyError):
        policy.validate_step(step(tool="shell.run", risk=RiskLevel.PROHIBITED), {"shell.run"})
    with pytest.raises(AgentPolicyError):
        policy.validate_step(step(), set())


def test_policy_forces_persistent_approval_and_retry_rules():
    policy = AgentPolicy()
    item = step(tool="reminder.create", risk=RiskLevel.READ_ONLY)
    policy.validate_step(item, {"reminder.create"})
    assert item.risk_level is RiskLevel.PERSISTENT
    assert item.approval_required
    assert not policy.can_retry(item, 1)
    assert policy.can_retry(step(), 1)
    assert not policy.can_retry(step(), 2)


def test_capability_snapshot_is_sorted_filtered_and_schema_only():
    registry = Registry()
    snapshot = AgentPolicy().capability_snapshot(registry)
    assert snapshot[0].name == "reminder.list"
    assert snapshot[0].read_only
    assert not hasattr(snapshot[0], "execute")


def test_planner_parses_typed_output_and_repairs_once():
    calls = []

    def generator(_context, repair):
        calls.append(repair)
        if len(calls) == 1:
            return "not json"
        return {"summary": "Özet", "steps": [{"step_id": "1", "title": "Listele", "tool_name": "reminder.list", "typed_arguments": {}}]}

    planner = AgentPlanner(AgentPolicy(), generator)
    result = planner.plan(AgentContext("listele", capabilities=(capability(),)))
    assert result.steps[0].tool_name == "reminder.list"
    assert len(calls) == 2


def test_planner_rejects_prohibited_request():
    with pytest.raises(AgentPolicyError):
        AgentPlanner(AgentPolicy()).plan(AgentContext("PowerShell çalıştır", capabilities=(capability(),)))


def test_deterministic_planner_builds_persistent_reminder_with_typed_arguments():
    result = AgentPlanner(AgentPolicy()).plan(AgentContext(
        "Agent modunda yarın saat 18:00 spor yapmayı hatırlat",
        capabilities=(capability("reminder.create", RiskLevel.PERSISTENT),),
    ))
    item = result.steps[0]
    assert item.tool_name == "reminder.create"
    assert item.approval_required
    assert isinstance(item.typed_arguments["due_at"], datetime)


def test_executor_validates_schema_and_normalizes_exception():
    registry = SafeToolRegistry()
    registry.register(ToolDefinition("memory.recall", IntentType.MEMORY_RECALL, "test", {"query": str}, False, lambda _r, _c: (_ for _ in ()).throw(RuntimeError("secret"))))
    executor = AgentExecutor(registry, 0.2)
    from lina.agent.models import CancellationToken
    from lina.brain.routing.models import RequestContext
    invalid = executor.execute(AgentStep("1", "x", "x", "memory.recall", {}), RequestContext(None), CancellationToken())
    assert invalid.error_code == "invalid_arguments"
    failed = executor.execute(AgentStep("2", "x", "x", "memory.recall", {"query": "x"}), RequestContext(None), CancellationToken())
    assert failed.error_code == "internal_error"
    assert "secret" not in failed.summary
    executor.shutdown()


@pytest.mark.parametrize(("result", "expected"), [
    (ExecutionResult(True, "ok", {"id": 1}), VerificationStatus.VERIFIED),
    (ExecutionResult(True, "model says ok", None), VerificationStatus.UNCERTAIN),
    (ExecutionResult(False, "no", None), VerificationStatus.FAILED),
])
def test_verifier_requires_typed_evidence(result, expected):
    assert AgentVerifier().verify(step(), result).status is expected


def test_created_id_verification_checks_expected_fields():
    item = step(rule=VerificationRule("created_id", {"title": "ders"}))
    assert AgentVerifier().verify(item, ExecutionResult(True, "ok", {"id": 1, "title": "ders"})).status is VerificationStatus.VERIFIED
    assert AgentVerifier().verify(item, ExecutionResult(True, "ok", {"id": 1, "title": "başka"})).status is VerificationStatus.FAILED


@pytest.mark.parametrize(("text", "decision"), [
    ("evet", ApprovalDecision.APPROVE), ("Onayla!", ApprovalDecision.APPROVE),
    ("atla", ApprovalDecision.SKIP), ("hayır", ApprovalDecision.SKIP),
    ("planı düzenle", ApprovalDecision.MODIFY), ("iptal et", ApprovalDecision.CANCEL),
    ("belki", ApprovalDecision.AMBIGUOUS), ("evet ama hayır", ApprovalDecision.AMBIGUOUS),
])
def test_approval_variants(text, decision):
    assert parse_approval(text) is decision


def controller(registry=None, generated_plan=None):
    registry = registry or Registry()
    policy = AgentPolicy()
    generator = lambda _context, _repair: generated_plan or {"summary": "Özet", "steps": [{"step_id": "1", "title": "Listele", "tool_name": registry.names()[0], "typed_arguments": {}, "risk_level": "persistent" if "create" in registry.names()[0] else "read_only"}]}
    return AgentController(AgentPlanner(policy, generator), AgentExecutor(registry), AgentVerifier(), policy)


def start(ctl):
    session = ctl.create_session("Agent modunda yap", 1, 3)
    ctl.plan()
    ctl.approve_plan(session.session_id, 3)
    return session


def test_controller_complete_flow_and_single_session():
    ctl = controller()
    start(ctl)
    with pytest.raises(AgentStateError):
        ctl.create_session("ikinci", 1)
    result = ctl.run(1)
    assert result.status is AgentSessionStatus.COMPLETED
    assert result.plan.steps[0].status is AgentStepStatus.SUCCEEDED
    assert result.metrics.executed_step_count == 1
    ctl.shutdown()


def test_controller_persistent_step_requires_separate_approval():
    registry = Registry(persistent=True, data={"id": 1})
    ctl = controller(registry)
    session = start(ctl)
    assert ctl.run().status is AgentSessionStatus.AWAITING_STEP_APPROVAL
    assert registry.calls == 0
    done = ctl.approve_step(session.session_id, ApprovalDecision.APPROVE, 3)
    assert done.status is AgentSessionStatus.COMPLETED
    assert registry.calls == 1
    ctl.shutdown()


def test_controller_ambiguous_skip_cancel_and_stale_guards():
    ctl = controller(Registry(persistent=True, data={"id": 1}))
    session = start(ctl)
    ctl.run()
    assert ctl.approve_step(session.session_id, ApprovalDecision.AMBIGUOUS).status is AgentSessionStatus.AWAITING_STEP_APPROVAL
    with pytest.raises(AgentStateError):
        ctl.approve_step("wrong", ApprovalDecision.APPROVE)
    done = ctl.approve_step(session.session_id, ApprovalDecision.SKIP)
    assert done.status is AgentSessionStatus.PARTIALLY_COMPLETED
    other = ctl.create_session("new", 2)
    assert ctl.cancel(other.session_id).status is AgentSessionStatus.CANCELLED
    ctl.shutdown()


def test_controller_pause_resume_and_conversation_isolation():
    ctl = controller()
    session = start(ctl)
    ctl.pause(session.session_id)
    with pytest.raises(AgentStateError):
        ctl.run(2)
    assert ctl.resume(session.session_id).status is AgentSessionStatus.COMPLETED
    ctl.shutdown()


def test_controller_failure_is_safe_and_persistent_not_retried():
    registry = Registry(fail=True, persistent=True)
    ctl = controller(registry)
    session = start(ctl)
    ctl.run()
    done = ctl.approve_step(session.session_id, ApprovalDecision.APPROVE)
    assert done.status is AgentSessionStatus.FAILED
    assert registry.calls == 1
    ctl.shutdown()
