from __future__ import annotations

import threading
import time

import pytest

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


def make_controller(enabled=True, barge_in=True):
    provider = BlockingProvider()
    playback = AudioPlaybackService(provider)
    controller = VoiceController(
        playback,
        settings=VoiceSettings(enabled=enabled, barge_in_enabled=barge_in),
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
    with pytest.raises(ValueError):
        controller.begin_transcribing()


def test_speaking_and_barge_in_stop_playback():
    controller, provider = make_controller()
    assert controller.speak_response("Merhaba")
    assert provider.started.wait(1)
    assert controller.state is VoiceState.SPEAKING
    assert controller.begin_listening()
    assert provider.stops == 1
    assert controller.state is VoiceState.LISTENING


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
