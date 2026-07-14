from __future__ import annotations

import threading
import time

from lina.voice.controller import VoiceController
from lina.voice.models import SystemVoice, VoiceSettings, VoiceState
from lina.voice.playback import AudioPlaybackService


class BlockingProvider:
    def __init__(self):
        self.started = threading.Event()
        self.release = threading.Event()
        self.stops = 0
        self.texts = []

    def is_available(self):
        return True

    def list_voices(self):
        return (SystemVoice("tr", "Türkçe", "tr"),)

    def speak(self, text, voice_id, rate, volume):
        self.texts.append(text)
        self.started.set()
        self.release.wait(1)

    def stop(self):
        self.stops += 1
        self.release.set()


class FakeWakeDetector:
    def __init__(self):
        self.callback = None
        self.running = False
        self.phrase = None
        self.device_id = None
        self.shutdowns = 0

    def is_available(self):
        return True

    def is_running(self):
        return self.running

    def start(self, callback=None):
        self.callback = callback or self.callback
        self.running = True
        return True

    def stop(self):
        self.running = False

    def set_phrase(self, phrase):
        self.phrase = phrase

    def set_device(self, device_id):
        self.device_id = device_id

    def shutdown(self):
        self.shutdowns += 1
        self.running = False

    def detect(self):
        self.callback()


def make_controller(enabled=True, barge_in=True):
    provider = BlockingProvider()
    playback = AudioPlaybackService(provider)
    controller = VoiceController(
        playback,
        settings=VoiceSettings(
            enabled=enabled,
            responses_enabled=enabled,
            barge_in_enabled=barge_in,
        ),
    )
    return controller, provider


def test_disabled_default_rejects_listening_and_speaking():
    controller, provider = make_controller(enabled=False)
    assert controller.state is VoiceState.DISABLED
    assert not controller.begin_listening()
    assert not controller.speak_response("Merhaba")
    assert not provider.started.is_set()


def test_valid_listen_transcribe_think_flow():
    controller, _ = make_controller()
    assert controller.begin_listening()
    controller.begin_transcribing()
    controller.begin_thinking()
    assert controller.state is VoiceState.THINKING
    controller.finish_interaction()
    assert controller.state is VoiceState.IDLE


def test_invalid_transition_is_rejected():
    controller, _ = make_controller()
    controller.begin_transcribing()
    assert controller.state is VoiceState.IDLE


def test_speaking_and_barge_in_stop_playback():
    controller, provider = make_controller()
    assert controller.speak_response("Merhaba")
    assert provider.started.wait(1)
    assert controller.state is VoiceState.SPEAKING
    assert controller.begin_listening()
    assert provider.stops == 1
    assert controller.state is VoiceState.LISTENING


def test_thinking_transitions_to_speaking_then_idle():
    controller, provider = make_controller()
    controller.begin_thinking()
    assert controller.state is VoiceState.THINKING
    assert controller.speak("Merhaba")
    assert provider.started.wait(1)
    assert controller.state is VoiceState.SPEAKING
    provider.release.set()
    for _ in range(20):
        if controller.state is VoiceState.IDLE:
            break
        time.sleep(0.01)
    assert controller.state is VoiceState.IDLE


def test_barge_in_can_be_disabled():
    controller, provider = make_controller(barge_in=False)
    controller.speak_response("Merhaba")
    assert provider.started.wait(1)
    assert not controller.begin_listening()
    assert provider.stops == 0
    controller.shutdown()


def test_stale_playback_callback_cannot_reset_new_state():
    controller, provider = make_controller()
    controller.speak_response("Birinci")
    assert provider.started.wait(1)
    controller.begin_listening()
    time.sleep(0.03)
    assert controller.state is VoiceState.LISTENING


def test_duplicate_stop_and_shutdown_are_safe():
    controller, provider = make_controller()
    controller.speak_response("Merhaba")
    assert provider.started.wait(1)
    assert controller.stop()
    assert not controller.stop()
    controller.shutdown()
    controller.shutdown()
    assert not controller.speak_response("sonra")


def test_voice_list_and_unavailable_wake_word_contract():
    controller, _ = make_controller()
    assert controller.list_voices()[0].language == "tr"
    assert not controller.wake_word_available


def test_voice_responses_disabled_skips_speak_even_when_mic_is_enabled():
    provider = BlockingProvider()
    controller = VoiceController(
        AudioPlaybackService(provider),
        settings=VoiceSettings(enabled=True, responses_enabled=False),
    )
    assert not controller.speak("Merhaba")
    assert controller.state is VoiceState.IDLE
    assert not provider.started.is_set()


def test_live_vision_feedback_can_speak_when_chat_voice_responses_are_disabled():
    provider = BlockingProvider()
    controller = VoiceController(
        AudioPlaybackService(provider),
        settings=VoiceSettings(enabled=True, responses_enabled=False),
    )
    assert controller.speak_live_vision("Elinde bir su şişesi var.")
    assert provider.started.wait(1)
    assert provider.texts == ["Elinde bir su şişesi var."]
    controller.shutdown()


def test_tts_lifecycle_logging_is_privacy_safe(caplog):
    controller, provider = make_controller()
    with caplog.at_level("INFO", logger="lina.voice"):
        assert controller.speak("gizli kullanıcı metni")
        assert provider.started.wait(1)
        provider.release.set()
        time.sleep(0.03)
    log_text = caplog.text
    assert "tts_requested" in log_text
    # Only the WinRT state bridge may report real playback lifecycle events.
    assert "playback_started" not in log_text
    assert "playback_completed" not in log_text
    assert "gizli kullanıcı metni" not in log_text


def test_tts_failure_log_contains_only_safe_category(caplog):
    class FailingProvider(BlockingProvider):
        def speak(self, text, voice_id, rate, volume):
            raise RuntimeError("private engine detail")

    controller = VoiceController(
        AudioPlaybackService(FailingProvider()),
        settings=VoiceSettings(enabled=True, responses_enabled=True),
    )
    with caplog.at_level("INFO", logger="lina.voice"):
        assert controller.speak("gizli metin")
        for _ in range(20):
            if controller.state is VoiceState.ERROR:
                break
            time.sleep(0.01)
    assert "tts_failed error_category=synthesis" in caplog.text
    assert "gizli metin" not in caplog.text
    assert "private engine detail" not in caplog.text


def test_hands_free_disabled_by_default_does_not_start_detector():
    wake = FakeWakeDetector()
    controller = VoiceController(
        AudioPlaybackService(BlockingProvider()),
        wake_word=wake,
        settings=VoiceSettings(enabled=True),
    )
    controller.configure(VoiceSettings(enabled=True))
    assert not wake.running
    assert controller.state is VoiceState.IDLE


def test_hands_free_start_detect_pause_resume_and_shutdown():
    wake = FakeWakeDetector()
    controller = VoiceController(
        AudioPlaybackService(BlockingProvider()),
        wake_word=wake,
        settings=VoiceSettings(enabled=True),
    )
    detected = []
    controller.subscribe_wake_detected(lambda: detected.append(True))
    settings = VoiceSettings(
        enabled=True,
        hands_free_enabled=True,
        wake_word_enabled=True,
        wake_phrase="Hey Lina",
        microphone_device_id=4,
    )
    controller.configure(settings)
    assert controller.state is VoiceState.WAKE_LISTENING
    assert wake.phrase == "Hey Lina"
    assert wake.device_id == 4
    wake.detect()
    assert detected == [True]
    assert controller.state is VoiceState.WAKE_DETECTED
    assert controller.begin_listening()
    assert controller.state is VoiceState.COMMAND_LISTENING
    assert controller.pause_hands_free()
    assert controller.state is VoiceState.IDLE
    assert controller.resume_hands_free()
    assert controller.state is VoiceState.WAKE_LISTENING
    controller.shutdown()
    assert wake.shutdowns == 1


def test_hands_free_speaking_enters_cooldown_then_restarts_wake(monkeypatch):
    class ImmediateTimer:
        daemon = False

        def __init__(self, _delay, callback):
            self.callback = callback

        def start(self):
            self.callback()

        def cancel(self):
            return None

    monkeypatch.setattr("lina.voice.controller.threading.Timer", ImmediateTimer)
    provider = BlockingProvider()
    wake = FakeWakeDetector()
    controller = VoiceController(
        AudioPlaybackService(provider),
        wake_word=wake,
        settings=VoiceSettings(
            enabled=True,
            hands_free_enabled=True,
            wake_word_enabled=True,
        ),
    )
    controller.configure(controller._settings)
    assert controller.speak("Merhaba")
    assert provider.started.wait(1)
    provider.release.set()
    for _ in range(100):
        if controller.state is VoiceState.WAKE_LISTENING:
            break
        time.sleep(0.005)
    assert controller.state is VoiceState.WAKE_LISTENING


def test_hands_free_barge_in_requires_wake_phrase_and_stales_playback():
    provider = BlockingProvider()
    wake = FakeWakeDetector()
    controller = VoiceController(
        AudioPlaybackService(provider),
        wake_word=wake,
        settings=VoiceSettings(
            enabled=True,
            hands_free_enabled=True,
            wake_word_enabled=True,
            barge_in_enabled=True,
        ),
    )
    detected = []
    controller.subscribe_wake_detected(lambda: detected.append(True))
    controller.configure(controller._settings)
    assert controller.speak("Normal assistant yanıtı")
    assert provider.started.wait(1)
    assert wake.running
    wake.detect()
    assert provider.stops == 1
    assert controller.state is VoiceState.WAKE_DETECTED
    assert detected == [True]


def test_hands_free_barge_in_disabled_pauses_detector_during_speech():
    provider = BlockingProvider()
    wake = FakeWakeDetector()
    controller = VoiceController(
        AudioPlaybackService(provider),
        wake_word=wake,
        settings=VoiceSettings(
            enabled=True,
            hands_free_enabled=True,
            wake_word_enabled=True,
            barge_in_enabled=False,
        ),
    )
    controller.configure(controller._settings)
    assert controller.speak("Yanıt")
    assert provider.started.wait(1)
    assert not wake.running
    controller.shutdown()
