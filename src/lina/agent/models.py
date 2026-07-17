"""Framework-neutral typed models for user-controlled Agent Mode."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import Event
from typing import Any
from uuid import uuid4

from lina.agent.errors import AgentPlanError


HARD_MAX_STEPS = 12


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AgentStepStatus(str, Enum):
    PENDING = "pending"
    WAITING_APPROVAL = "waiting_approval"
    RUNNING = "running"
    VERIFYING = "verifying"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class AgentSessionStatus(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    AWAITING_PLAN_APPROVAL = "awaiting_plan_approval"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    AWAITING_STEP_APPROVAL = "awaiting_step_approval"
    REPLANNING = "replanning"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"
    INTERRUPTED = "interrupted"


class RiskLevel(str, Enum):
    READ_ONLY = "read_only"
    LOW = "low"
    PERSISTENT = "persistent"
    SENSITIVE = "sensitive"
    PROHIBITED = "prohibited"


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    FAILED = "failed"
    UNCERTAIN = "uncertain"


class ApprovalDecision(str, Enum):
    APPROVE = "approve"
    SKIP = "skip"
    MODIFY = "modify"
    CANCEL = "cancel"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True, slots=True)
class VerificationRule:
    kind: str = "typed_success"
    expected: dict[str, Any] = field(default_factory=dict)
    read_back_tool: str | None = None

    @classmethod
    def from_value(cls, value: object) -> "VerificationRule":
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return cls(value)
        if isinstance(value, dict):
            return cls(
                str(value.get("kind", "typed_success")),
                dict(value.get("expected", {})) if isinstance(value.get("expected", {}), dict) else {},
                str(value["read_back_tool"]) if value.get("read_back_tool") else None,
            )
        raise AgentPlanError("Geçersiz doğrulama kuralı.")


@dataclass(slots=True)
class AgentStep:
    step_id: str
    title: str
    description: str
    tool_name: str
    typed_arguments: dict[str, Any]
    risk_level: RiskLevel = RiskLevel.READ_ONLY
    approval_required: bool = False
    status: AgentStepStatus = AgentStepStatus.PENDING
    dependencies: tuple[str, ...] = ()
    verification_rule: VerificationRule = field(default_factory=VerificationRule)
    result_summary: str | None = None
    error_code: str | None = None
    execution_id: str | None = None

    def __post_init__(self) -> None:
        self.risk_level = RiskLevel(self.risk_level)
        self.status = AgentStepStatus(self.status)
        self.dependencies = tuple(self.dependencies)
        self.verification_rule = VerificationRule.from_value(self.verification_rule)
        if not self.step_id or not self.title.strip() or not self.tool_name.strip():
            raise AgentPlanError("Plan adımı kimlik, başlık ve araç içermeli.")
        if not isinstance(self.typed_arguments, dict):
            raise AgentPlanError("Plan adımı argümanları typed nesne olmalı.")


@dataclass(slots=True)
class AgentPlan:
    plan_id: str
    summary: str
    steps: list[AgentStep]
    estimated_step_count: int | None = None
    requires_approval: bool = True
    created_at: datetime = field(default_factory=utc_now)
    revision: int = 1
    template_id: str | None = None
    title: str | None = None
    risk_summary: str = ""

    def __post_init__(self) -> None:
        self.steps = list(self.steps)
        self.estimated_step_count = len(self.steps) if self.estimated_step_count is None else self.estimated_step_count
        self.title = (self.title or self.summary).strip()
        self.validate()

    def validate(self, maximum_steps: int = HARD_MAX_STEPS) -> None:
        if not self.plan_id or not self.summary.strip() or not self.steps:
            raise AgentPlanError("Plan özeti ve en az bir adım gerekli.")
        if len(self.steps) > min(maximum_steps, HARD_MAX_STEPS):
            raise AgentPlanError("Plan güvenli adım sınırını aşıyor.")
        ids = [step.step_id for step in self.steps]
        if len(ids) != len(set(ids)):
            raise AgentPlanError("Plan içinde yinelenen adım kimliği var.")
        known: set[str] = set()
        graph = {step.step_id: set(step.dependencies) for step in self.steps}
        for step in self.steps:
            if step.step_id in step.dependencies or not set(step.dependencies).issubset(set(ids)):
                raise AgentPlanError("Plan geçersiz bir adım bağımlılığı içeriyor.")
            known.add(step.step_id)
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> None:
            if node in visiting:
                raise AgentPlanError("Plan döngüsel bağımlılık içeriyor.")
            if node in visited:
                return
            visiting.add(node)
            for dependency in graph[node]:
                visit(dependency)
            visiting.remove(node)
            visited.add(node)

        for step_id in ids:
            visit(step_id)


@dataclass(slots=True)
class AgentMetrics:
    planned_step_count: int = 0
    executed_step_count: int = 0
    succeeded_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    approval_count: int = 0
    replan_count: int = 0
    cancellation_count: int = 0
    step_duration_ms: list[int] = field(default_factory=list)

    def safe_dict(self) -> dict[str, Any]:
        durations = self.step_duration_ms
        return {
            "planned_step_count": self.planned_step_count,
            "executed_step_count": self.executed_step_count,
            "succeeded_count": self.succeeded_count,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "approval_count": self.approval_count,
            "replan_count": self.replan_count,
            "cancellation_count": self.cancellation_count,
            "average_step_duration_ms": round(sum(durations) / len(durations)) if durations else 0,
        }


class CancellationToken:
    def __init__(self) -> None:
        self._event = Event()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()

    def cancel(self) -> None:
        self._event.set()


@dataclass(slots=True)
class AgentSession:
    session_id: str
    conversation_id: int | None
    user_request: str
    status: AgentSessionStatus = AgentSessionStatus.IDLE
    plan: AgentPlan | None = None
    current_step_index: int = 0
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    approval_state: str | None = None
    cancellation_token: CancellationToken = field(default_factory=CancellationToken)
    metrics: AgentMetrics = field(default_factory=AgentMetrics)
    generation_id: int = 0

    @classmethod
    def create(cls, conversation_id: int | None, user_request: str) -> "AgentSession":
        return cls(uuid4().hex, conversation_id, user_request.strip())

    def touch(self) -> None:
        self.updated_at = utc_now()

    @property
    def terminal(self) -> bool:
        return self.status in {
            AgentSessionStatus.COMPLETED, AgentSessionStatus.PARTIALLY_COMPLETED,
            AgentSessionStatus.FAILED, AgentSessionStatus.CANCELLED,
            AgentSessionStatus.BLOCKED, AgentSessionStatus.INTERRUPTED,
        }


@dataclass(frozen=True, slots=True)
class CapabilitySnapshot:
    name: str
    description: str
    allowed_arguments: tuple[tuple[str, str], ...]
    result_type: str
    risk_level: RiskLevel
    approval_required: bool
    available: bool
    read_only: bool


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    success: bool
    summary: str
    data: Any = None
    error_code: str | None = None
    execution_id: str = field(default_factory=lambda: uuid4().hex)
    duration_ms: int = 0
    retryable: bool = False


@dataclass(frozen=True, slots=True)
class VerificationResult:
    status: VerificationStatus
    summary: str


def safe_value(value: Any, depth: int = 0) -> Any:
    """Serialize metadata without retaining raw tool payloads or binary data."""
    if depth > 3:
        return "<truncated>"
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str):
        return value[:240]
    if isinstance(value, (bytes, bytearray, memoryview)):
        return "<binary omitted>"
    if isinstance(value, dict):
        return {str(key)[:64]: safe_value(item, depth + 1) for key, item in list(value.items())[:20]}
    if isinstance(value, (list, tuple)):
        return [safe_value(item, depth + 1) for item in value[:20]]
    return f"<{type(value).__name__}>"
