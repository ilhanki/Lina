"""Safe, typed Agent Mode failures."""

from enum import Enum


class AgentErrorCode(str, Enum):
    TOOL_UNAVAILABLE = "tool_unavailable"
    INVALID_ARGUMENTS = "invalid_arguments"
    PERMISSION_DENIED = "permission_denied"
    APPROVAL_REQUIRED = "approval_required"
    USER_CANCELLED = "user_cancelled"
    TIMEOUT = "timeout"
    TRANSIENT_FAILURE = "transient_failure"
    PERSISTENT_OUTCOME_UNCERTAIN = "persistent_outcome_uncertain"
    VERIFICATION_FAILED = "verification_failed"
    VERIFICATION_UNCERTAIN = "verification_uncertain"
    DEPENDENCY_FAILED = "dependency_failed"
    LOOP_DETECTED = "loop_detected"
    STEP_LIMIT_REACHED = "step_limit_reached"
    REPLAN_LIMIT_REACHED = "replan_limit_reached"
    STALE_RESULT = "stale_result"
    INTERRUPTED = "interrupted"
    PROHIBITED = "prohibited"
    UNSUPPORTED_REQUEST = "unsupported_request"
    STORAGE_FAILURE = "storage_failure"
    INTERNAL_ERROR = "internal_error"


class AgentError(Exception):
    """Base error whose message is safe to show to the user."""


class AgentPlanError(AgentError):
    pass


class AgentClarificationRequired(AgentPlanError):
    def __init__(self, message: str, missing_parameters: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.missing_parameters = tuple(missing_parameters)


class AgentPolicyError(AgentError):
    pass


class AgentExecutionError(AgentError):
    def __init__(self, message: str, code: str | AgentErrorCode = AgentErrorCode.INTERNAL_ERROR) -> None:
        super().__init__(message)
        self.code = AgentErrorCode(code)


class AgentStateError(AgentError):
    pass
