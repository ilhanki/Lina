"""Independent least-privilege policy for Agent Mode."""

from __future__ import annotations

from lina.agent.errors import AgentPolicyError
from lina.agent.models import AgentPlan, AgentStep, CapabilitySnapshot, RiskLevel


READ_ONLY_TOOLS = frozenset({
    "reminder.list", "memory.recall", "files.read", "vision.image",
    "vision.screen", "vision.region", "live_vision.live_vision_status",
    "system.status", "model.status", "datetime.now", "notification.list",
    "conversation.search",
})
PERSISTENT_TOOLS = frozenset({
    "reminder.create", "reminder.update", "memory.store", "memory.update",
    "notification.settings.update", "application.settings.update",
})
PROHIBITED_PREFIXES = (
    "shell", "cmd", "powershell", "process", "browser", "email", "message",
    "git", "mouse", "keyboard", "system.settings", "files.write", "files.delete",
    "files.move", "files.rename", "camera.start", "microphone.start", "code.execute",
)


class AgentPolicy:
    HARD_MAX_STEPS = 12

    def __init__(self, max_steps: int = 8, max_replans: int = 1, max_step_retries: int = 1) -> None:
        if not 3 <= max_steps <= self.HARD_MAX_STEPS:
            raise ValueError("Agent maximum steps must be between 3 and 12")
        self.max_steps = max_steps
        self.max_replans = min(max(max_replans, 0), 1)
        self.max_step_retries = min(max(max_step_retries, 0), 1)

    def risk_for(self, tool_name: str, declared: RiskLevel | None = None) -> RiskLevel:
        normalized = tool_name.casefold()
        if any(normalized == prefix or normalized.startswith(prefix + ".") for prefix in PROHIBITED_PREFIXES):
            return RiskLevel.PROHIBITED
        if tool_name in PERSISTENT_TOOLS:
            return RiskLevel.PERSISTENT
        if tool_name in READ_ONLY_TOOLS:
            return RiskLevel.READ_ONLY
        return declared or RiskLevel.PROHIBITED

    def validate_step(self, step: AgentStep, available_tools: set[str]) -> None:
        risk = self.risk_for(step.tool_name, step.risk_level)
        if step.tool_name not in available_tools:
            raise AgentPolicyError("Gerekli araç şu anda kullanılamıyor.")
        if risk is RiskLevel.PROHIBITED:
            raise AgentPolicyError("Bu işlem Agent Mode yetkilerinin dışında.")
        step.risk_level = risk
        step.approval_required = risk in {RiskLevel.PERSISTENT, RiskLevel.SENSITIVE} or step.approval_required

    def validate_plan(self, plan: AgentPlan, available_tools: set[str]) -> None:
        plan.validate(self.max_steps)
        seen: set[tuple[str, str]] = set()
        for step in plan.steps:
            self.validate_step(step, available_tools)
            signature = (step.tool_name, repr(sorted(step.typed_arguments.items())))
            if signature in seen:
                raise AgentPolicyError("Plan aynı adımı tekrar etmeye başladı. Güvenlik için görev durduruldu.")
            seen.add(signature)

    @staticmethod
    def requires_step_approval(step: AgentStep) -> bool:
        return step.approval_required or step.risk_level in {RiskLevel.PERSISTENT, RiskLevel.SENSITIVE}

    def can_retry(self, step: AgentStep, attempts: int) -> bool:
        return step.risk_level is RiskLevel.READ_ONLY and attempts <= self.max_step_retries

    def capability_snapshot(self, registry: object) -> tuple[CapabilitySnapshot, ...]:
        definitions = getattr(registry, "definitions", lambda: ())()
        result: list[CapabilitySnapshot] = []
        for definition in sorted(definitions, key=lambda item: item.name):
            risk = self.risk_for(definition.name)
            if risk is RiskLevel.PROHIBITED:
                continue
            available = bool(definition.available())
            result.append(CapabilitySnapshot(
                name=definition.name,
                description=str(definition.description)[:240],
                allowed_arguments=tuple(sorted((name, kind.__name__) for name, kind in definition.input_schema.items())),
                result_type="ToolResult",
                risk_level=risk,
                approval_required=risk in {RiskLevel.PERSISTENT, RiskLevel.SENSITIVE},
                available=available,
                read_only=risk is RiskLevel.READ_ONLY,
            ))
        return tuple(result)
