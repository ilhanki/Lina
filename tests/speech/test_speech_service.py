"""Tests for speech capability orchestration."""

import pytest

from lina.speech.models import (
    SpeechServiceError,
    SpeechState,
    SpeechSynthesisResult,
    SpeechTranscriptionResult,
)
from lina.speech.providers import NoOpSTTProvider, NoOpTTSProvider
from lina.speech.service import SpeechService


class FakeSTTProvider:
    def __init__(self, error: Exception | None = None) -> None:
        self._error = error
        self.call_count = 0

    def is_available(self) -> bool:
        return True

    def transcribe_once(self) -> SpeechTranscriptionResult:
        self.call_count += 1
        if self._error is not None:
            raise self._error
        return SpeechTranscriptionResult(
            text="Merhaba Lina",
            confidence=0.95,
            source="fake",
            is_final=True,
        )


class FakeTTSProvider:
    def __init__(self) -> None:
        self.spoken_texts: list[str] = []
        self.stop_count = 0

    def is_available(self) -> bool:
        return True

    def speak(self, text: str) -> SpeechSynthesisResult:
        self.spoken_texts.append(text)
        return SpeechSynthesisResult(success=True)

    def stop(self) -> None:
        self.stop_count += 1


def _create_service(
    stt_provider=None,
    tts_provider=None,
) -> SpeechService:
    return SpeechService(
        stt_provider=stt_provider or NoOpSTTProvider(),
        tts_provider=tts_provider or NoOpTTSProvider(),
    )


def test_default_noop_stt_is_unavailable() -> None:
    service = _create_service()

    assert service.is_stt_available() is False

    with pytest.raises(SpeechServiceError, match="unavailable"):
        service.transcribe_once()

    assert service.get_state() is SpeechState.UNAVAILABLE


def test_default_noop_tts_is_unavailable() -> None:
    service = _create_service()

    result = service.speak("Hello")

    assert service.is_tts_available() is False
    assert result.success is False
    assert result.message == "Text-to-speech provider is unavailable"
    assert service.get_state() is SpeechState.UNAVAILABLE


def test_transcribe_once_returns_fake_provider_result() -> None:
    provider = FakeSTTProvider()
    service = _create_service(stt_provider=provider)

    result = service.transcribe_once()

    assert result.text == "Merhaba Lina"
    assert provider.call_count == 1
    assert service.get_state() is SpeechState.IDLE


def test_transcribe_once_does_not_send_or_transform_text() -> None:
    service = _create_service(stt_provider=FakeSTTProvider())

    result = service.transcribe_once()

    assert result == SpeechTranscriptionResult(
        text="Merhaba Lina",
        confidence=0.95,
        source="fake",
        is_final=True,
    )


def test_provider_exception_does_not_leave_transcription_state_stuck() -> None:
    service = _create_service(stt_provider=FakeSTTProvider(RuntimeError("failure")))

    with pytest.raises(SpeechServiceError, match="transcription failed"):
        service.transcribe_once()

    assert service.get_state() is SpeechState.ERROR


def test_speak_uses_available_provider_and_returns_to_idle() -> None:
    provider = FakeTTSProvider()
    service = _create_service(tts_provider=provider)

    result = service.speak("Hello")

    assert result.success is True
    assert provider.spoken_texts == ["Hello"]
    assert service.get_state() is SpeechState.IDLE


def test_stop_speaking_calls_provider_stop() -> None:
    provider = FakeTTSProvider()
    service = _create_service(tts_provider=provider)

    service.stop_speaking()

    assert provider.stop_count == 1
    assert service.get_state() is SpeechState.IDLE
