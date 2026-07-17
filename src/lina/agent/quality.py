"""Deterministic quality checks for generated and edited Agent plans."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from lina.agent.models import AgentPlan, RiskLevel


class PlanQualityIssueCode(str, Enum):
    VAGUE_STEP = "vague_step"
    DUPLICATE_STEP = "duplicate_step"
    MISSING_TOOL = "missing_tool"
    PERSISTENT_APPROVAL_MISSING = "persistent_approval_missing"
    INVALID_VERIFICATION = "invalid_verification"
    IRRELEVANT_STEP = "irrelevant_step"


@dataclass(frozen=True, slots=True)
class PlanQualityIssue:
    code: PlanQualityIssueCode
    step_id: str
    summary: str


@dataclass(frozen=True, slots=True)
class PlanQualityResult:
    valid: bool
    issues: tuple[PlanQualityIssue, ...]
    normalized_plan: AgentPlan
    repair_required: bool


class AgentPlanQualityValidator:
    def validate(self, plan: AgentPlan, *, allowed_tools: set[str]) -> PlanQualityResult:
        issues: list[PlanQualityIssue] = []
        signatures: set[tuple[str, str]] = set()
        vague = {"yap", "işle", "devam et", "kontrol et", "tamamla", "doğrula"}
        for step in plan.steps:
            title = " ".join(step.title.casefold().split()).strip(" .!?")
            if title in vague or len(title) < 4:
                issues.append(PlanQualityIssue(PlanQualityIssueCode.VAGUE_STEP, step.step_id, "Adım yeterince açık değil."))
            if not step.tool_name or step.tool_name not in allowed_tools:
                issues.append(PlanQualityIssue(PlanQualityIssueCode.MISSING_TOOL, step.step_id, "Adım için kullanılabilir araç yok."))
            signature = (step.tool_name, repr(sorted(step.typed_arguments.items())))
            if signature in signatures:
                issues.append(PlanQualityIssue(PlanQualityIssueCode.DUPLICATE_STEP, step.step_id, "Aynı işlem planda tekrar ediyor."))
            signatures.add(signature)
            if step.risk_level in {RiskLevel.PERSISTENT, RiskLevel.SENSITIVE} and not step.approval_required:
                issues.append(PlanQualityIssue(PlanQualityIssueCode.PERSISTENT_APPROVAL_MISSING, step.step_id, "Kalıcı adım onay gerektirmeli."))
            if step.verification_rule.kind not in {"typed_success", "success", "non_empty", "created_id"}:
                issues.append(PlanQualityIssue(PlanQualityIssueCode.INVALID_VERIFICATION, step.step_id, "Doğrulama kuralı deterministic değil."))
        return PlanQualityResult(not issues, tuple(issues), plan, bool(issues))
