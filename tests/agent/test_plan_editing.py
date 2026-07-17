from datetime import datetime, timedelta, timezone

import pytest

from lina.agent import (
    AgentPlan,
    AgentPlanEditor,
    AgentPlanQualityValidator,
    AgentPolicy,
    AgentStep,
    AgentStepStatus,
    RiskLevel,
    diff_plans,
    render_plan_diff,
)
from lina.agent.errors import AgentPlanError, AgentPolicyError


def _step(
    step_id: str,
    *,
    tool: str = "reminder.list",
    risk: RiskLevel = RiskLevel.READ_ONLY,
    dependencies=(),
    optional=False,
    arguments=None,
):
    return AgentStep(
        step_id,
        f"{step_id} adımını çalıştır",
        "Güvenli adım",
        tool,
        {"scope": step_id} if arguments is None else arguments,
        risk,
        risk is RiskLevel.PERSISTENT,
        dependencies=dependencies,
        optional=optional,
    )


def _plan(*steps):
    return AgentPlan("p", "Güvenli plan", list(steps or (_step("one"),)))


def _editor(*tools, schemas=None):
    return AgentPlanEditor(AgentPolicy(), set(tools or ("reminder.list",)), schemas)


def test_remove_optional_step_and_diff():
    before = _plan(_step("required"), _step("optional", optional=True))
    after, difference = _editor().remove_optional_step(before, "optional")
    assert [step.step_id for step in after.steps] == ["required"]
    assert difference.removed_steps == ("optional",)
    assert before.revision == 1 and after.revision == 2
    assert "1 adım kaldırıldı" in render_plan_diff(difference)


def test_required_or_dependency_step_cannot_be_removed_or_skipped():
    editor = _editor()
    before = _plan(_step("one"), _step("two", dependencies=("one",), optional=True))
    with pytest.raises(AgentPolicyError, match="opsiyonel"):
        editor.remove_optional_step(before, "one")
    with pytest.raises(AgentPolicyError, match="Bağımlı"):
        editor.skip_step(before, "one")


def test_skip_optional_leaf_step_marks_it_without_execution():
    before = _plan(_step("one"), _step("two", optional=True))
    after, difference = _editor().skip_step(before, "two")
    assert after.steps[1].status is AgentStepStatus.SKIPPED
    assert "two" in difference.modified_steps


def test_reorder_preserves_dependency_order_and_rejects_invalid_order():
    before = _plan(_step("one"), _step("two"), _step("three", dependencies=("one",)))
    after, difference = _editor().reorder(before, ("two", "one", "three"))
    assert [step.step_id for step in after.steps] == ["two", "one", "three"]
    assert difference.reordered_steps
    with pytest.raises(AgentPlanError, match="bağımlılık"):
        _editor().reorder(before, ("three", "one", "two"))
    with pytest.raises(AgentPlanError, match="tüm adımları"):
        _editor().reorder(before, ("one", "two"))


def test_update_arguments_requires_exact_typed_tool_schema():
    before = _plan(_step("one", tool="reminder.create", risk=RiskLevel.PERSISTENT, arguments={"title": "eski", "due_at": datetime.now(timezone.utc), "recurrence": "none"}))
    schemas = {"reminder.create": {"title": str, "due_at": datetime, "recurrence": str}}
    editor = _editor("reminder.create", schemas=schemas)
    due_at = datetime.now(timezone.utc) + timedelta(hours=1)
    after, difference = editor.update_arguments(before, "one", {"title": "yeni", "due_at": due_at.isoformat(), "recurrence": "none"})
    assert after.steps[0].typed_arguments["title"] == "yeni"
    assert isinstance(after.steps[0].typed_arguments["due_at"], datetime)
    assert difference.modified_steps == ("one",)
    with pytest.raises(AgentPolicyError, match="schema"):
        editor.update_arguments(before, "one", {"title": "yeni", "extra": "yasak"})


def test_update_arguments_rejects_empty_past_naive_and_invalid_enum_values():
    before = _plan(_step("one", tool="reminder.create", risk=RiskLevel.PERSISTENT, arguments={"title": "eski", "due_at": datetime.now(timezone.utc) + timedelta(hours=1), "recurrence": "none"}))
    schemas = {"reminder.create": {"title": str, "due_at": datetime, "recurrence": str}}
    editor = _editor("reminder.create", schemas=schemas)
    with pytest.raises(AgentPolicyError, match="boş"):
        editor.update_arguments(before, "one", {"title": " ", "due_at": datetime.now(timezone.utc) + timedelta(hours=1), "recurrence": "none"})
    with pytest.raises(AgentPolicyError, match="gelecekte"):
        editor.update_arguments(before, "one", {"title": "x", "due_at": datetime.now(timezone.utc) - timedelta(minutes=1), "recurrence": "none"})
    with pytest.raises(AgentPolicyError, match="saat dilimi"):
        editor.update_arguments(before, "one", {"title": "x", "due_at": datetime.now() + timedelta(hours=1), "recurrence": "none"})
    with pytest.raises(AgentPolicyError, match="Tekrarlama"):
        editor.update_arguments(before, "one", {"title": "x", "due_at": datetime.now(timezone.utc) + timedelta(hours=1), "recurrence": "monthly"})


def test_replace_step_cannot_lower_risk_remove_approval_or_add_prohibited_tool():
    original = _plan(_step("one", tool="reminder.create", risk=RiskLevel.PERSISTENT))
    editor = _editor("reminder.create", "shell.run")
    lowered = _step("one", tool="reminder.list", risk=RiskLevel.READ_ONLY)
    with pytest.raises(AgentPolicyError, match="risk"):
        editor.replace_step(original, "one", lowered)
    no_approval = AgentStep("one", "Hatırlatıcı oluştur", "Oluştur", "reminder.create", {}, RiskLevel.PERSISTENT, False)
    with pytest.raises(AgentPolicyError, match="onayı"):
        editor.replace_step(original, "one", no_approval)
    prohibited = AgentStep("one", "Shell çalıştır", "Yasak", "shell.run", {}, RiskLevel.PROHIBITED, True)
    with pytest.raises(AgentPolicyError, match="yetkilerinin dışında"):
        editor.replace_step(original, "one", prohibited)


def test_regenerate_preserves_completed_steps_and_reports_new_approval():
    completed = _step("done")
    completed.status = AgentStepStatus.SUCCEEDED
    old = _plan(completed, _step("old"))
    new = _plan(_step("new", tool="reminder.create", risk=RiskLevel.PERSISTENT))
    editor = _editor("reminder.list", "reminder.create")
    edited, difference = editor.regenerate(old, new)
    assert edited.steps[0].status is AgentStepStatus.SUCCEEDED
    assert difference.preserved_completed_steps == ("done",)
    assert difference.added_steps == ("new",)


def test_diff_covers_modified_reordered_risk_and_approval_changes():
    before = _plan(_step("one"), _step("two"))
    after = _plan(_step("two"), _step("one", tool="reminder.create", risk=RiskLevel.PERSISTENT))
    difference = diff_plans(before, after)
    assert difference.modified_steps == ("one",)
    assert set(difference.reordered_steps) == {"one", "two"}
    assert difference.risk_changes == ("one",)
    assert difference.new_approvals == ("one",)
    assert "yeni kalıcı işlem onayı" in render_plan_diff(difference)


def test_plan_quality_detects_vague_duplicate_missing_approval_and_bad_verification():
    first = AgentStep("one", "Yap", "belirsiz", "reminder.list", {})
    second = AgentStep("two", "Tekrar kontrol et", "tekrar", "reminder.list", {})
    persistent = AgentStep("three", "Hatırlatıcı oluştur", "kalıcı", "reminder.create", {}, RiskLevel.PERSISTENT, False, verification_rule="model_says_ok")
    result = AgentPlanQualityValidator().validate(_plan(first, second, persistent), allowed_tools={"reminder.list", "reminder.create"})
    codes = {issue.code.value for issue in result.issues}
    assert {"vague_step", "duplicate_step", "persistent_approval_missing", "invalid_verification"}.issubset(codes)
    assert result.repair_required


def test_plan_quality_accepts_clear_valid_plan():
    result = AgentPlanQualityValidator().validate(_plan(_step("one")), allowed_tools={"reminder.list"})
    assert result.valid
    assert not result.repair_required
