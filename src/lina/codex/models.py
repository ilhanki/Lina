"""Typed, persistence-safe models for the user-controlled Codex bridge."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CodexSessionStatus(str, Enum):
    CREATED = "created"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    WAITING_APPROVAL = "waiting_approval"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"


class CodexRiskLevel(str, Enum):
    READ_ONLY = "read_only"
    ANALYSIS = "analysis"
    SUGGESTION = "suggestion"
    MODIFICATION = "modification"


class WorkspacePermissionLevel(str, Enum):
    ONE_TIME = "one_time"
    SESSION = "session"
    REMEMBERED = "remembered"


class CodexExecutionMode(str, Enum):
    PLAN_ONLY = "plan_only"
    READ_ONLY = "read_only"
    CONTROLLED_MODIFICATION = "controlled_modification"


class CodexEventType(str, Enum):
    SESSION_STARTED = "session_started"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    FILE_SCANNED = "file_scanned"
    SUGGESTION_READY = "suggestion_ready"
    APPROVAL_REQUESTED = "approval_requested"
    MODIFICATION_STARTED = "modification_started"
    MODIFICATION_COMPLETED = "modification_completed"
    COMMAND_REQUESTED = "command_requested"
    COMMAND_COMPLETED = "command_completed"
    MESSAGE_DELTA = "message_delta"
    MESSAGE_COMPLETED = "message_completed"
    USAGE = "usage"
    VERIFICATION_STARTED = "verification_started"
    COMPLETED = "completed"
    FAILED = "failed"


class VerificationOutcome(str, Enum):
    SUCCESS = "success"
    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    UNVERIFIED = "unverified"
    UNCERTAIN = "uncertain"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ProjectContext:
    root_path: Path
    allowed_files: tuple[Path, ...] = ()
    project_type: str = "unknown"
    detected_languages: tuple[str, ...] = ()
    framework_hints: tuple[str, ...] = ()
    git_status_summary: str = "unavailable"

    def __post_init__(self) -> None:
        object.__setattr__(self, "root_path", self.root_path.expanduser().resolve())
        object.__setattr__(self, "allowed_files", tuple(Path(item).resolve() for item in self.allowed_files))


@dataclass(frozen=True, slots=True)
class RequestedAction:
    name: str
    target: str = ""
    purpose: str = ""


@dataclass(frozen=True, slots=True)
class ExpectedOutput:
    description: str
    required_artifacts: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CodexVerificationRule:
    kind: str
    target: str = ""
    expected: str = ""


@dataclass(slots=True)
class CodexTask:
    task_id: str
    title: str
    description: str
    objective: str
    workspace: Path
    requested_actions: tuple[RequestedAction, ...]
    risk_level: CodexRiskLevel = CodexRiskLevel.READ_ONLY
    approval_required: bool = False
    expected_output: ExpectedOutput = field(default_factory=lambda: ExpectedOutput("Özet"))
    verification_rules: tuple[CodexVerificationRule, ...] = ()

    def __post_init__(self) -> None:
        self.workspace = self.workspace.expanduser().resolve()
        self.requested_actions = tuple(self.requested_actions)
        self.risk_level = CodexRiskLevel(self.risk_level)
        self.verification_rules = tuple(self.verification_rules)
        if not self.task_id or not self.title.strip() or not self.objective.strip():
            raise ValueError("Codex görevi kimlik, başlık ve amaç içermeli.")
        if self.risk_level is CodexRiskLevel.MODIFICATION:
            self.approval_required = True

    @classmethod
    def create(
        cls, title: str, description: str, objective: str, workspace: Path,
        requested_actions: tuple[RequestedAction, ...], **kwargs: object,
    ) -> "CodexTask":
        return cls(uuid4().hex, title, description, objective, workspace, requested_actions, **kwargs)


@dataclass(slots=True)
class CodexSession:
    session_id: str
    agent_session_id: str | None
    conversation_id: int | None
    project_context: ProjectContext
    status: CodexSessionStatus
    created_at: datetime
    updated_at: datetime
    permission_level: WorkspacePermissionLevel
    execution_mode: CodexExecutionMode
    task_summary: str
    task: CodexTask | None = None
    progress: int = 0
    result_summary: str = ""
    error_code: str | None = None
    cli_version: str | None = None
    approval_decision: str = "pending"
    verification_outcome: str = "unverified"
    duration_seconds: float = 0.0
    exit_category: str = "not_started"

    @classmethod
    def create(
        cls, project_context: ProjectContext, task_summary: str,
        conversation_id: int | None = None, agent_session_id: str | None = None,
        permission_level: WorkspacePermissionLevel = WorkspacePermissionLevel.ONE_TIME,
        execution_mode: CodexExecutionMode = CodexExecutionMode.READ_ONLY,
    ) -> "CodexSession":
        now = utc_now()
        return cls(uuid4().hex, agent_session_id, conversation_id, project_context,
                   CodexSessionStatus.CREATED, now, now, permission_level,
                   execution_mode, task_summary.strip())

    @property
    def terminal(self) -> bool:
        return self.status in {CodexSessionStatus.COMPLETED, CodexSessionStatus.FAILED,
                               CodexSessionStatus.CANCELLED, CodexSessionStatus.INTERRUPTED}

    def transition(self, status: CodexSessionStatus, progress: int | None = None) -> None:
        self.status = CodexSessionStatus(status)
        self.updated_at = utc_now()
        if progress is not None:
            self.progress = max(0, min(100, progress))


@dataclass(frozen=True, slots=True)
class CodexEvent:
    event_id: str
    session_id: str
    event_type: CodexEventType
    occurred_at: datetime
    message: str
    progress: int | None = None
    file_name: str | None = None

    @classmethod
    def create(cls, session_id: str, event_type: CodexEventType, message: str = "",
               progress: int | None = None, file_name: str | None = None) -> "CodexEvent":
        return cls(uuid4().hex, session_id, event_type, utc_now(), message[:240], progress, file_name)


@dataclass(frozen=True, slots=True)
class CodexExecutionEvidence:
    exit_code: int | None = None
    before_fingerprints: tuple[tuple[str, str], ...] = ()
    after_fingerprints: tuple[tuple[str, str], ...] = ()
    tests_passed: bool | None = None
    sensitive_output_detected: bool = False


@dataclass(frozen=True, slots=True)
class CodexResult:
    summary: str
    artifacts: tuple[str, ...] = ()
    changed_files: tuple[str, ...] = ()
    verification_notes: tuple[str, ...] = ()
    stale: bool = False
    evidence: CodexExecutionEvidence | None = None


@dataclass(frozen=True, slots=True)
class VerificationReport:
    outcome: VerificationOutcome
    summary: str
    checks: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CodexHistoryEntry:
    session_id: str
    task_summary: str
    created_at: datetime
    status: CodexSessionStatus
    result_summary: str
    workspace_hash: str = ""
    operation_type: str = "unknown"
    risk: str = "unknown"
    approval_decision: str = "unknown"
    cli_version: str | None = None
    verification: str = "unverified"
    duration_seconds: float = 0.0
    exit_category: str = "unknown"
