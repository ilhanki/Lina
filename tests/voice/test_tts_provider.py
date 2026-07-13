from __future__ import annotations

import time

import pytest
from PySide6.QtTextToSpeech import QTextToSpeech

from lina.voice.models import SystemVoice, VoiceUnavailableError
from lina.voice.tts_provider import (
    UnavailableTTSProvider,
    QtWindowsTTSProvider,
    WindowsSapiTTSProvider,
    _QtSpeechBridge,
    _clamp_volume,
    normalize_spoken_text,
)


class FakeToken:
    Id = "tr-voice"

    def GetDescription(self):
        return "Microsoft Emel - Turkish"


class FakeVoices:
    Count = 1

    def Item(self, index):
        assert index == 0
        return FakeToken()


class FakeSpeaker:
    def __init__(self):
        self.Rate = 0
        self.Volume = 0
        self.Voice = None
        self.spoken = []

    def GetVoices(self):
        return FakeVoices()

    def Speak(self, text, flags):
        self.spoken.append((text, flags))

    def WaitUntilDone(self, timeout):
        return True


class FakeLocale:
    def name(self):
        return "tr_TR"


class FakeQtVoice:
    def name(self):
        return "Microsoft Tolga"

    def locale(self):
        return FakeLocale()


class FakeQtEngine:
    def state(self):
        return type("State", (), {"name": "Ready"})()

    def availableVoices(self):
        return [FakeQtVoice()]

    def setVoice(self, voice):
        self.selected_voice = voice


def test_normalize_spoken_text_removes_code_urls_json_and_base64():
    text = "Merhaba. ```python\nprint('secret')\n``` https://example.com/" + "a" * 80
    text += "\n{" + '"key":"' + "A" * 130 + '"}'
    spoken = normalize_spoken_text(text)
    assert "Merhaba" in spoken
    assert "print" not in spoken
    assert "https://" not in spoken
    assert "A" * 100 not in spoken


def test_normalize_spoken_text_truncates_without_changing_input():
    original = "Türkçe yanıt " * 100
    spoken = normalize_spoken_text(original, max_characters=80)
    assert len(spoken) < len(original)
    assert spoken.endswith("Yanıtın devamı ekranda.")
    assert original.startswith("Türkçe yanıt")


def test_unavailable_provider_is_safe():
    provider = UnavailableTTSProvider()
    assert not provider.is_available()
    assert provider.list_voices() == ()
    provider.stop()
    with pytest.raises(VoiceUnavailableError):
        provider.speak("Merhaba", None, 1.0, 1.0)


def test_windows_provider_lists_and_uses_turkish_voice():
    speaker = FakeSpeaker()
    provider = WindowsSapiTTSProvider(dispatch=lambda _name: speaker)
    voices = provider.list_voices()
    assert voices[0].language == "tr"
    provider.speak("Merhaba dünya", None, 1.4, 0.6)
    assert speaker.Voice.Id == "tr-voice"
    assert speaker.Rate == 2
    assert speaker.Volume == 60
    assert speaker.spoken == [("Merhaba dünya", 1)]


def test_qt_windows_provider_discovers_turkish_system_voice():
    provider = QtWindowsTTSProvider(engine_factory=FakeQtEngine)
    assert provider.is_available()
    assert provider.list_voices() == (
        SystemVoice("Microsoft Tolga|tr_TR", "Microsoft Tolga", "tr"),
    )


def test_selected_winrt_voice_failure_retries_engine_default():
    engines = [FakeQtEngine(), FakeQtEngine()]

    class FallbackProvider(QtWindowsTTSProvider):
        attempts = 0

        def _speak_once(self, engine, *args):
            self.attempts += 1
            if self.attempts == 1:
                from lina.voice.models import VoicePlaybackError

                raise VoicePlaybackError("selected voice failed")

    provider = FallbackProvider(engine_factory=lambda: engines.pop(0))
    provider.speak("Merhaba", "Microsoft Tolga|tr_TR", 1.0, 1.0)
    assert provider.attempts == 2


def test_winrt_lifecycle_logs_only_real_state_transitions(monkeypatch, qtbot, caplog):
    monkeypatch.setattr(_QtSpeechBridge, "_replace_engine", lambda self: False)
    bridge = _QtSpeechBridge()
    bridge._request_id = 7
    bridge._started_at = time.monotonic()

    with caplog.at_level("INFO", logger="lina.voice"):
        bridge._about_to_synthesize(1)
        bridge._state_changed(QTextToSpeech.State.Synthesizing)
        assert "playback_started" not in caplog.text
        bridge._state_changed(QTextToSpeech.State.Speaking)
        assert "playback_started" in caplog.text
        assert "playback_completed" not in caplog.text
        bridge._state_changed(QTextToSpeech.State.Ready)

    assert "playback_completed" in caplog.text
    assert "audio_bytes=not_exposed" in caplog.text
    assert "mime=audio/winrt-direct" in caplog.text


def test_winrt_error_log_is_privacy_safe(monkeypatch, qtbot, caplog):
    monkeypatch.setattr(_QtSpeechBridge, "_replace_engine", lambda self: False)
    bridge = _QtSpeechBridge()
    outcomes = []
    bridge.finished.connect(lambda request_id, success, category: outcomes.append((request_id, success, category)))
    bridge._request_id = 9

    with caplog.at_level("INFO", logger="lina.voice"):
        bridge._error_occurred(QTextToSpeech.ErrorReason.Playback, "private media detail")

    assert outcomes == [(9, False, "playback")]
    assert "tts_engine_error error_category=playback" in caplog.text
    assert "private media detail" not in caplog.text


def test_winrt_stop_cleans_active_request_without_false_completion(monkeypatch, qtbot, caplog):
    monkeypatch.setattr(_QtSpeechBridge, "_replace_engine", lambda self: False)
    bridge = _QtSpeechBridge()
    outcomes = []

    class Engine:
        def stop(self):
            bridge._state_changed(QTextToSpeech.State.Ready)

    bridge._engine = Engine()
    bridge._request_id = 11
    bridge._playing = True
    bridge.finished.connect(lambda request_id, success, category: outcomes.append((request_id, success, category)))

    with caplog.at_level("INFO", logger="lina.voice"):
        bridge._stop()

    assert outcomes == [(11, False, "cancelled")]
    assert bridge._request_id == 0
    assert "playback_completed" not in caplog.text


@pytest.mark.parametrize(("raw", "expected"), [(-2.0, 0.0), (0.5, 0.5), (2.0, 1.0)])
def test_qt_volume_is_clamped_to_documented_bounds(raw, expected):
    assert _clamp_volume(raw) == expected
