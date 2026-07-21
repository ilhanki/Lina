"""Framework-neutral priority and stale-callback protection for UI status."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class StatusPriority(IntEnum):
    BACKGROUND = 10
    UNAVAILABLE = 20
    DISABLED = 30
    READY = 40
    ACTIVE = 50
    THINKING = 50
    VISION = 60
    AGENT = 70
    CODEX = 80
    SPEAKING = 90
    TRANSCRIBING = 100
    LISTENING = 110
    RUNTIME_APPROVAL = 120
    ATTENTION = 130
    SECURITY = 140
    ERROR = 150


@dataclass(frozen=True, slots=True)
class UnifiedStatus:
    text: str
    priority: StatusPriority
    generation: int
    secondary: tuple[str, ...] = ()


class UnifiedStatusController:
    def __init__(self) -> None:
        self._current = UnifiedStatus("Hazır", StatusPriority.READY, 0)

    @property
    def current(self) -> UnifiedStatus:
        return self._current

    def publish(self, text: str, *, priority: StatusPriority = StatusPriority.ACTIVE, generation: int | None = None, secondary: tuple[str, ...] = ()) -> bool:
        candidate_generation = self._current.generation + 1 if generation is None else generation
        if candidate_generation < self._current.generation:
            return False
        if (
            candidate_generation == self._current.generation
            and priority < self._current.priority
        ):
            return False
        self._current = UnifiedStatus(text, priority, candidate_generation, secondary)
        return True
