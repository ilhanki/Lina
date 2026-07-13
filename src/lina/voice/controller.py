"""Voice state machine, playback lifecycle and barge-in coordination."""

from __future__ import annotations

from collections.abc import Callable
import threading

from lina.voice.models import VoiceSettings, VoiceState
from lina.voice.playback import AudioPlaybackService
from lina.voice.tts_provider import normalize_spoken_text
from lina.voice.wake_word import UnavailableWakeWordDetector, WakeWordDetector


StateListener = Callable[[VoiceState], None]


class VoiceController:
    def __init__(self, playback: AudioPlaybackService, wake_word: WakeWordDetector | None = None, settings: VoiceSettings | None = None) -> None:
        self._playback = playback
        self._wake_word = wake_word or UnavailableWakeWordDetector()
        self._settings = settings or VoiceSettings()
        self._state = VoiceState.IDLE if self._settings.enabled else VoiceState.DISABLED
        self._listeners: list[StateListener] = []
        self._lock = threading.RLock()
        self._shutdown = False

    @property
    def state(self) -> VoiceState:
        with self._lock:
            return self._state

    @property
    def wake_word_available(self) -> bool:
        return self._wake_word.is_available()

    @property
    def tts_available(self) -> bool:
        return self._playback.is_available

    def list_voices(self):
        return self._playback.list_voices()

    def subscribe(self, listener: StateListener) -> None:
        if listener not in self._listeners:
            self._listeners.append(listener)

    def configure(self, settings: VoiceSettings) -> None:
        self._settings = settings
        if not settings.enabled:
            self.stop()
            self._set_state(VoiceState.DISABLED)
        elif self.state is VoiceState.DISABLED:
            self._set_state(VoiceState.IDLE)

    def begin_listening(self) -> bool:
        if self._shutdown:
            return False
        if self.state is VoiceState.SPEAKING:
            if not self._settings.barge_in_enabled:
                return False
            self._playback.stop()
            self._set_state(VoiceState.INTERRUPTED)
        if self.state is VoiceState.DISABLED:
            return False
        self._set_state(VoiceState.LISTENING)
        return True

    def begin_transcribing(self) -> None:
        self._transition({VoiceState.LISTENING}, VoiceState.TRANSCRIBING)

    def begin_thinking(self) -> None:
        self._transition({VoiceState.LISTENING, VoiceState.TRANSCRIBING, VoiceState.IDLE}, VoiceState.THINKING)

    def speak_response(self, text: str) -> bool:
        if self._shutdown or not self._settings.enabled:
            return False
        spoken = normalize_spoken_text(text)
        if not spoken:
            self._set_state(VoiceState.IDLE)
            return False
        self._set_state(VoiceState.SPEAKING)
        self._playback.play(
            spoken,
            self._settings.voice_id,
            self._settings.rate,
            self._settings.volume,
            self._playback_finished,
        )
        return True

    def _playback_finished(self, generation: int, result: object) -> None:
        if self._shutdown:
            return
        self._set_state(VoiceState.IDLE if getattr(result, "completed", False) else VoiceState.ERROR)

    def stop(self) -> bool:
        stopped = self._playback.stop()
        if self.state is VoiceState.SPEAKING:
            self._set_state(VoiceState.INTERRUPTED)
        return stopped

    def finish_interaction(self) -> None:
        if self.state is not VoiceState.DISABLED:
            self._set_state(VoiceState.IDLE)

    def shutdown(self) -> None:
        self._shutdown = True
        self._wake_word.stop()
        self._playback.shutdown()
        self._listeners.clear()

    def _transition(self, allowed: set[VoiceState], target: VoiceState) -> None:
        if self.state not in allowed:
            raise ValueError(f"Invalid voice transition: {self.state.value} -> {target.value}")
        self._set_state(target)

    def _set_state(self, state: VoiceState) -> None:
        with self._lock:
            if state is self._state:
                return
            self._state = state
        for listener in tuple(self._listeners):
            try:
                listener(state)
            except Exception:
                continue
