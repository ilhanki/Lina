from __future__ import annotations

import pytest

from lina.voice.models import VoiceUnavailableError
from lina.voice.tts_provider import (
    UnavailableTTSProvider,
    WindowsSapiTTSProvider,
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
