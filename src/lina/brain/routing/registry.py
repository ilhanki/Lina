"""Central allowlist of safe assistant tools."""

from dataclasses import dataclass
from typing import Any, Callable

from lina.brain.routing.models import IntentRequest, IntentType, RequestContext, ToolResult


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    name: str
    intent: IntentType
    description: str
    input_schema: dict[str, type]
    requires_confirmation: bool
    execute: Callable[[IntentRequest, RequestContext], ToolResult]
    available: Callable[[], bool] = lambda: True
    unavailable_message: str = "Bu araç şu anda kullanılamıyor."


class SafeToolRegistry:
    def __init__(self) -> None:
        self._by_intent: dict[IntentType, ToolDefinition] = {}

    def register(self, definition: ToolDefinition) -> None:
        if definition.intent in self._by_intent:
            raise ValueError(f"Intent already registered: {definition.intent.value}")
        self._by_intent[definition.intent] = definition

    def get(self, intent: IntentType) -> ToolDefinition | None:
        return self._by_intent.get(intent)

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(item.name for item in self._by_intent.values()))
