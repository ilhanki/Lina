"""Validated plan editing and human-readable plan differences."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import uuid4

from lina.agent.errors import AgentPlanError, AgentPolicyError
from lina.agent.models import AgentPlan, AgentStep, AgentStepStatus, RiskLevel
from lina.agent.policy import AgentPolicy


@dataclass(frozen=True, slots=True)
class AgentPlanDiff:
    added_steps: tuple[str, ...] = ()
    removed_steps: tuple[str, ...] = ()
    modified_steps: tuple[str, ...] = ()
    reordered_steps: tuple[str, ...] = ()
    risk_changes: tuple[str, ...] = ()
    new_approvals: tuple[str, ...] = ()
    preserved_completed_steps: tuple[str, ...] = ()

    @property
    def changed(self) -> bool:
        return any((self.added_steps, self.removed_steps, self.modified_steps, self.reordered_steps, self.risk_changes, self.new_approvals))


class AgentPlanEditor:
    def __init__(
        self,
        policy: AgentPolicy,
        available_tools: set[str],
        tool_schemas: dict[str, dict[str, type | tuple[type, ...]]] | None = None,
    ) -> None:
        self.policy = policy
        self.available_tools = set(available_tools)
        self.tool_schemas = tool_schemas or {}

    def remove_optional_step(self, plan: AgentPlan, step_id: str) -> tuple[AgentPlan, AgentPlanDiff]:
        edited = deepcopy(plan)
        step = _require_step(edited, step_id)
        if not step.optional:
            raise AgentPolicyError("Yalnız opsiyonel plan adımları kaldırılabilir.")
        if step.status in {AgentStepStatus.RUNNING, AgentStepStatus.VERIFYING, AgentStepStatus.SUCCEEDED}:
            raise AgentPolicyError("Başlamış veya tamamlanmış plan adımı kaldırılamaz.")
        if any(step_id in item.dependencies for item in edited.steps):
            raise AgentPolicyError("Başka bir adımın bağlı olduğu plan adımı kaldırılamaz.")
        edited.steps = [item for item in edited.steps if item.step_id != step_id]
        return self._finalize(plan, edited)

    def skip_step(self, plan: AgentPlan, step_id: str) -> tuple[AgentPlan, AgentPlanDiff]:
        edited = deepcopy(plan)
        step = _require_step(edited, step_id)
        if step.status in {AgentStepStatus.RUNNING, AgentStepStatus.VERIFYING, AgentStepStatus.SUCCEEDED}:
            raise AgentPolicyError("Başlamış veya tamamlanmış plan adımı atlanamaz.")
        if any(step_id in item.dependencies and item.status is AgentStepStatus.PENDING for item in edited.steps):
            raise AgentPolicyError("Bağımlı adımlar varken bu plan adımı atlanamaz.")
        step.status = AgentStepStatus.SKIPPED
        step.result_summary = "Kullanıcı plan incelemesinde atladı."
        return self._finalize(plan, edited)

    def reorder(self, plan: AgentPlan, ordered_step_ids: tuple[str, ...] | list[str]) -> tuple[AgentPlan, AgentPlanDiff]:
        requested = tuple(ordered_step_ids)
        existing = tuple(step.step_id for step in plan.steps)
        if len(requested) != len(existing) or set(requested) != set(existing):
            raise AgentPlanError("Yeni sıra plandaki tüm adımları tam olarak içermeli.")
        by_id = {step.step_id: deepcopy(step) for step in plan.steps}
        positions = {step_id: index for index, step_id in enumerate(requested)}
        for step in plan.steps:
            if any(positions[dependency] > positions[step.step_id] for dependency in step.dependencies):
                raise AgentPlanError("Yeni sıra adım bağımlılıklarını bozuyor.")
        edited = deepcopy(plan)
        edited.steps = [by_id[step_id] for step_id in requested]
        return self._finalize(plan, edited)

    def update_arguments(self, plan: AgentPlan, step_id: str, arguments: dict[str, Any]) -> tuple[AgentPlan, AgentPlanDiff]:
        edited = deepcopy(plan)
        step = _require_step(edited, step_id)
        if step.status is not AgentStepStatus.PENDING:
            raise AgentPolicyError("Yalnız bekleyen adımın girdisi düzenlenebilir.")
        schema = self.tool_schemas.get(step.tool_name)
        if schema is None:
            raise AgentPolicyError("Bu araç için düzenlenebilir typed schema bulunamadı.")
        _validate_arguments(arguments, schema)
        step.typed_arguments = dict(arguments)
        return self._finalize(plan, edited)

    def replace_step(self, plan: AgentPlan, step_id: str, replacement: AgentStep) -> tuple[AgentPlan, AgentPlanDiff]:
        """Validated low-level edit used by UI forms and planner repairs."""
        edited = deepcopy(plan)
        original = _require_step(edited, step_id)
        if original.status is not AgentStepStatus.PENDING:
            raise AgentPolicyError("Yalnız bekleyen plan adımı değiştirilebilir.")
        risk_rank = {
            RiskLevel.READ_ONLY: 0,
            RiskLevel.LOW: 1,
            RiskLevel.PERSISTENT: 2,
            RiskLevel.SENSITIVE: 3,
            RiskLevel.PROHIBITED: 4,
        }
        if risk_rank[replacement.risk_level] < risk_rank[original.risk_level]:
            raise AgentPolicyError("Plan adımının risk seviyesi düşürülemez.")
        if original.approval_required and not replacement.approval_required:
            raise AgentPolicyError("Gerekli kalıcı işlem onayı kaldırılamaz.")
        index = edited.steps.index(original)
        edited.steps[index] = deepcopy(replacement)
        return self._finalize(plan, edited)

    def regenerate(self, old_plan: AgentPlan, new_plan: AgentPlan) -> tuple[AgentPlan, AgentPlanDiff]:
        preserved = [deepcopy(step) for step in old_plan.steps if step.status is AgentStepStatus.SUCCEEDED]
        preserved_ids = {step.step_id for step in preserved}
        generated = deepcopy(new_plan)
        generated.steps = preserved + [step for step in generated.steps if step.step_id not in preserved_ids]
        return self._finalize(old_plan, generated)

    def _finalize(self, original: AgentPlan, edited: AgentPlan) -> tuple[AgentPlan, AgentPlanDiff]:
        edited.plan_id = uuid4().hex
        edited.revision = original.revision + 1
        edited.estimated_step_count = len(edited.steps)
        edited.validate(self.policy.max_steps)
        self.policy.validate_plan(edited, self.available_tools)
        return edited, diff_plans(original, edited)


def diff_plans(before: AgentPlan, after: AgentPlan) -> AgentPlanDiff:
    old = {step.step_id: step for step in before.steps}
    new = {step.step_id: step for step in after.steps}
    old_order = [step.step_id for step in before.steps]
    new_order = [step.step_id for step in after.steps]
    shared = set(old) & set(new)
    modified = []
    risk_changes = []
    new_approvals = []
    preserved = []
    for step_id in sorted(shared):
        left, right = old[step_id], new[step_id]
        if _step_payload(left) != _step_payload(right):
            modified.append(step_id)
        if left.risk_level is not right.risk_level:
            risk_changes.append(step_id)
        if not left.approval_required and right.approval_required:
            new_approvals.append(step_id)
        if left.status is AgentStepStatus.SUCCEEDED and right.status is AgentStepStatus.SUCCEEDED:
            preserved.append(step_id)
    reordered = tuple(step_id for step_id in new_order if step_id in shared and old_order.index(step_id) != new_order.index(step_id))
    return AgentPlanDiff(
        added_steps=tuple(step_id for step_id in new_order if step_id not in old),
        removed_steps=tuple(step_id for step_id in old_order if step_id not in new),
        modified_steps=tuple(modified),
        reordered_steps=reordered,
        risk_changes=tuple(risk_changes),
        new_approvals=tuple(new_approvals),
        preserved_completed_steps=tuple(preserved),
    )


def render_plan_diff(diff: AgentPlanDiff) -> str:
    if not diff.changed:
        return "Plan değişmedi."
    changes: list[str] = []
    if diff.added_steps:
        changes.append(f"{len(diff.added_steps)} adım eklendi")
    if diff.removed_steps:
        changes.append(f"{len(diff.removed_steps)} adım kaldırıldı")
    if diff.modified_steps:
        changes.append(f"{len(diff.modified_steps)} adım güncellendi")
    if diff.reordered_steps:
        changes.append("adım sırası değiştirildi")
    if diff.risk_changes:
        changes.append("risk özeti güncellendi")
    if diff.new_approvals:
        changes.append("yeni kalıcı işlem onayı gerekiyor")
    return "Plan güncellendi: " + ", ".join(changes) + "."


def _require_step(plan: AgentPlan, step_id: str) -> AgentStep:
    step = next((item for item in plan.steps if item.step_id == step_id), None)
    if step is None:
        raise AgentPlanError("Plan adımı bulunamadı.")
    return step


def _validate_arguments(arguments: dict[str, Any], schema: dict[str, type | tuple[type, ...]]) -> None:
    if set(arguments) != set(schema):
        raise AgentPolicyError("Araç girdileri typed schema ile eşleşmiyor.")
    for name, kind in schema.items():
        value = arguments[name]
        if kind is datetime and isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError as error:
                raise AgentPolicyError(f"'{name}' girdisi geçersiz.") from error
            arguments[name] = value
    from lina.agent.templates.validators import TemplateInputError, validate_parameters

    try:
        validate_parameters(schema, arguments)
    except TemplateInputError as error:
        raise AgentPolicyError(str(error)) from error


def _step_payload(step: AgentStep) -> tuple[object, ...]:
    return (
        step.title,
        step.description,
        step.tool_name,
        repr(sorted(step.typed_arguments.items())),
        step.risk_level,
        step.approval_required,
        step.dependencies,
        step.verification_rule,
        step.status,
    )
