"""Bounded and privacy-safe context passed to a planner."""

from dataclasses import dataclass

from lina.agent.models import CapabilitySnapshot


@dataclass(frozen=True, slots=True)
class AgentContext:
    user_request: str
    recent_messages: tuple[str, ...] = ()
    relevant_memories: tuple[str, ...] = ()
    capabilities: tuple[CapabilitySnapshot, ...] = ()
    completed_step_summaries: tuple[str, ...] = ()

    @classmethod
    def bounded(cls, user_request: str, recent_messages=(), relevant_memories=(), capabilities=(), completed=()):
        clean = lambda values, count: tuple(str(value)[:500] for value in tuple(values)[-count:])
        return cls(user_request[:2000], clean(recent_messages, 12), clean(relevant_memories, 5), tuple(capabilities), clean(completed, 12))
