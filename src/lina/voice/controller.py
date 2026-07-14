"""Voice state machine, playback lifecycle and barge-in coordination."""

from __future__ import annotations

from collections.abc import Callable
import logging
import threading

from lina.voice.models import VoiceSettings, VoiceState
from lina.voice.playback import AudioPlaybackService
from lina.voice.state_machine import VoiceStateMachine
from lina.voice.tts_provider import normalize_spoken_text
from lina.voice.wake_word import UnavailableWakeWordDetector, WakeWordDetector
from lina.voice.wake_word import wake_phrase_matches


StateListener = Callable[[VoiceState], None]
_logger = logging.getLogger("lina.voice")


class VoiceController:
    def __init__(self, playback: AudioPlaybackService, wake_word: WakeWordDetector | None = None, settings: VoiceSettings | None = None) -> None:
        self._playback = playback
        self._wake_word = wake_word or UnavailableWakeWordDetector()
        self._settings = settings or VoiceSettings()
        self._machine = VoiceStateMachine(VoiceState.IDLE if self._settings.enabled else VoiceState.DISABLED)
        self._wake_listeners: list[Callable[[], None]] = []
        self._lock = threading.RLock()
        self._shutdown = False
        self._hands_free_paused = False
        self._cooldown_timer: threading.Timer | None = None
        self._command_after_cooldown = False

    @property
    def state(self) -> VoiceState:
        return self._machine.state

    @property
    def wake_word_available(self) -> bool:
        return self._wake_word.is_available()

    @property
    def tts_available(self) -> bool:
        return self._playback.is_available

    def list_voices(self):
        return self._playback.list_voices()

    def subscribe(self, listener: StateListener) -> None:
        self._machine.subscribe(listener)

    def subscribe_wake_detected(self, listener: Callable[[], None]) -> None:
        if listener not in self._wake_listeners:
            self._wake_listeners.append(listener)

    def configure(self, settings: VoiceSettings) -> None:
        self._settings = settings
        try:
            self._wake_word.set_phrase(settings.wake_phrase)
        except ValueError:
            _logger.warning("wake_configuration_failed error_category=invalid_phrase")
        set_device = getattr(self._wake_word, "set_device", None)
        if set_device is not None:
            set_device(settings.microphone_device_id)
        if not settings.enabled:
            self.stop()
            self._wake_word.stop()
            self._set_state(VoiceState.DISABLED, force=True)
        elif self.state is VoiceState.DISABLED:
            self._set_state(VoiceState.IDLE)
        if self.hands_free_enabled and not self._hands_free_paused:
            self.start_hands_free()
        elif not self.hands_free_enabled:
            self._wake_word.stop()
            if self.state is VoiceState.WAKE_LISTENING:
                self._set_state(VoiceState.IDLE)

    @property
    def hands_free_enabled(self) -> bool:
        return bool(
            self._settings.enabled
            and self._settings.hands_free_enabled
            and self._settings.wake_word_enabled
        )

    @property
    def hands_free_paused(self) -> bool:
        return self._hands_free_paused

    @property
    def voice_confirmation_enabled(self) -> bool:
        return self._settings.voice_confirmation_enabled

    def start_hands_free(self) -> bool:
        if self._shutdown or not self.hands_free_enabled or not self.wake_word_available:
            return False
        self._cancel_cooldown()
        self._hands_free_paused = False
        if not self._wake_word.start(self._handle_wake_detected):
            self._set_state(VoiceState.ERROR, force=True)
            return False
        self._set_state(VoiceState.WAKE_LISTENING, force=self.state is VoiceState.ERROR)
        return True

    def pause_hands_free(self) -> bool:
        if not self.hands_free_enabled:
            return False
        self._hands_free_paused = True
        self._cancel_cooldown()
        self._wake_word.stop()
        self._set_state(VoiceState.IDLE, force=True)
        return True

    def resume_hands_free(self) -> bool:
        self._hands_free_paused = False
        return self.start_hands_free()

    def request_confirmation_listening(self) -> bool:
        if not self.hands_free_enabled or not self._settings.voice_confirmation_enabled:
            return False
        self._command_after_cooldown = True
        return True

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
        self._set_state(VoiceState.COMMAND_LISTENING if self.hands_free_enabled else VoiceState.LISTENING)
        return True

    def begin_transcribing(self) -> None:
        self._transition({VoiceState.LISTENING, VoiceState.COMMAND_LISTENING}, VoiceState.TRANSCRIBING)

    def begin_thinking(self) -> None:
        self._transition({VoiceState.LISTENING, VoiceState.COMMAND_LISTENING, VoiceState.TRANSCRIBING, VoiceState.IDLE}, VoiceState.THINKING)

    @property
    def responses_enabled(self) -> bool:
        return self._settings.responses_enabled

    def speak(self, text: str) -> bool:
        if self._shutdown or not self._settings.enabled or not (self._settings.responses_enabled or self.hands_free_enabled):
            return False
        spoken = normalize_spoken_text(text)
        if not spoken:
            self._set_state(VoiceState.IDLE)
            return False
        _logger.info("tts_requested")
        if not self.tts_available:
            _logger.warning("tts_failed error_category=unavailable")
            self._finish_or_resume()
            return False
        if self.hands_free_enabled and self._settings.barge_in_enabled and not wake_phrase_matches(spoken, self._settings.wake_phrase):
            self._wake_word.start(self._handle_wake_detected)
        else:
            self._wake_word.stop()
        self._set_state(VoiceState.SPEAKING)
        self._playback.play(
            spoken,
            self._settings.voice_id,
            self._settings.rate,
            self._settings.volume,
            self._playback_finished,
        )
        return True

    def speak_response(self, text: str) -> bool:
        """Backward-compatible alias for final assistant response speech."""
        return self.speak(text)

    def _playback_finished(self, generation: int, result: object) -> None:
        if self._shutdown:
            return
        if getattr(result, "completed", False):
            self._finish_or_resume()
        else:
            self._set_state(VoiceState.ERROR)
            self._finish_or_resume()

    def stop(self) -> bool:
        stopped = self._playback.stop()
        if self.state is VoiceState.SPEAKING:
            self._set_state(VoiceState.INTERRUPTED)
        return stopped

    def finish_interaction(self) -> None:
        if self.state is not VoiceState.DISABLED:
            self._finish_or_resume()

    def shutdown(self) -> None:
        if self._shutdown:
            return
        self._shutdown = True
        self._cancel_cooldown()
        self._wake_word.shutdown()
        self._playback.shutdown()
        self._wake_listeners.clear()

    def _transition(self, allowed: set[VoiceState], target: VoiceState) -> None:
        if self.state not in allowed:
            _logger.warning("voice_transition_rejected from_state=%s to_state=%s", self.state.value, target.value)
            return
        self._set_state(target)

    def _set_state(self, state: VoiceState, *, force: bool = False) -> None:
        self._machine.transition(state, force=force)

    def _handle_wake_detected(self) -> None:
        if self._shutdown or self._hands_free_paused:
            return
        if self.state is VoiceState.SPEAKING and self._settings.barge_in_enabled:
            self._playback.stop()
            self._set_state(VoiceState.INTERRUPTED)
            self._wake_word.stop()
            self._set_state(VoiceState.WAKE_DETECTED, force=True)
        elif self.state is VoiceState.WAKE_LISTENING:
            self._wake_word.stop()
            if not self._machine.transition(VoiceState.WAKE_DETECTED):
                return
        else:
            return
        for listener in tuple(self._wake_listeners):
            try:
                listener()
            except Exception:
                continue

    def _finish_or_resume(self) -> None:
        if self.hands_free_enabled and self._settings.return_to_wake_listening and not self._hands_free_paused:
            self._wake_word.stop()
            self._set_state(VoiceState.COOLDOWN, force=self.state is VoiceState.ERROR)
            self._cancel_cooldown()
            callback = self._start_confirmation_command if self._command_after_cooldown else self.start_hands_free
            timer = threading.Timer(self._settings.cooldown_seconds, callback)
            timer.daemon = True
            self._cooldown_timer = timer
            timer.start()
        else:
            self._set_state(VoiceState.IDLE, force=True)

    def _start_confirmation_command(self) -> None:
        self._command_after_cooldown = False
        if self._shutdown or self._hands_free_paused or not self.hands_free_enabled:
            return
        self._set_state(VoiceState.WAKE_DETECTED, force=True)
        for listener in tuple(self._wake_listeners):
            try:
                listener()
            except Exception:
                continue

    def _cancel_cooldown(self) -> None:
        timer = self._cooldown_timer
        self._cooldown_timer = None
        if timer is not None:
            timer.cancel()
