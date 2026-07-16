"""Safe, typed Agent Mode failures."""


class AgentError(Exception):
    """Base error whose message is safe to show to the user."""


class AgentPlanError(AgentError):
    pass


class AgentPolicyError(AgentError):
    pass


class AgentExecutionError(AgentError):
    def __init__(self, message: str, code: str = "execution_error") -> None:
        super().__init__(message)
        self.code = code


class AgentStateError(AgentError):
    pass
