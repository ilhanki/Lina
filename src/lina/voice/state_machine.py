"""Typed, non-throwing state transitions for hands-free voice interaction."""

from __future__ import annotations

from collections.abc import Callable
import threading

from lina.voice.models import VoiceState


StateListener = Callable[[VoiceState], None]


_TRANSITIONS: dict[VoiceState, frozenset[VoiceState]] = {
    VoiceState.DISABLED: frozenset({VoiceState.IDLE}),
    VoiceState.IDLE: frozenset({VoiceState.DISABLED, VoiceState.LISTENING, VoiceState.WAKE_LISTENING, VoiceState.THINKING, VoiceState.SPEAKING}),
    VoiceState.LISTENING: frozenset({VoiceState.TRANSCRIBING, VoiceState.THINKING, VoiceState.IDLE, VoiceState.ERROR}),
    VoiceState.WAKE_LISTENING: frozenset({VoiceState.WAKE_DETECTED, VoiceState.SPEAKING, VoiceState.IDLE, VoiceState.DISABLED, VoiceState.ERROR}),
    VoiceState.WAKE_DETECTED: frozenset({VoiceState.COMMAND_LISTENING, VoiceState.COOLDOWN, VoiceState.ERROR}),
    VoiceState.COMMAND_LISTENING: frozenset({VoiceState.TRANSCRIBING, VoiceState.COOLDOWN, VoiceState.INTERRUPTED, VoiceState.ERROR}),
    VoiceState.TRANSCRIBING: frozenset({VoiceState.THINKING, VoiceState.COOLDOWN, VoiceState.IDLE, VoiceState.ERROR}),
    VoiceState.THINKING: frozenset({VoiceState.SPEAKING, VoiceState.COOLDOWN, VoiceState.IDLE, VoiceState.ERROR}),
    VoiceState.SPEAKING: frozenset({VoiceState.INTERRUPTED, VoiceState.COOLDOWN, VoiceState.IDLE, VoiceState.ERROR}),
    VoiceState.INTERRUPTED: frozenset({VoiceState.LISTENING, VoiceState.COMMAND_LISTENING, VoiceState.COOLDOWN, VoiceState.IDLE}),
    VoiceState.COOLDOWN: frozenset({VoiceState.WAKE_LISTENING, VoiceState.IDLE, VoiceState.DISABLED}),
    VoiceState.ERROR: frozenset({VoiceState.COOLDOWN, VoiceState.WAKE_LISTENING, VoiceState.IDLE, VoiceState.DISABLED}),
}


class VoiceStateMachine:
    """Own voice state and reject invalid transitions without crashing callers."""

    def __init__(self, initial: VoiceState = VoiceState.DISABLED) -> None:
        self._state = initial
        self._listeners: list[StateListener] = []
        self._lock = threading.RLock()

    @property
    def state(self) -> VoiceState:
        with self._lock:
            return self._state

    def subscribe(self, listener: StateListener) -> None:
        if listener not in self._listeners:
            self._listeners.append(listener)

    def unsubscribe(self, listener: StateListener) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    def transition(self, target: VoiceState, *, force: bool = False) -> bool:
        with self._lock:
            current = self._state
            if target is current:
                return True
            if not force and target not in _TRANSITIONS[current]:
                return False
            self._state = target
        for listener in tuple(self._listeners):
            try:
                listener(target)
            except Exception:
                continue
        return True
