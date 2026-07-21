"""Tests for speech capability orchestration."""

import pytest
import threading

from lina.speech.models import (
    AudioRecordingResult,
    SpeechServiceError,
    SpeechState,
    SpeechSynthesisResult,
    SpeechTranscriptionResult,
)
from lina.speech.providers import NoOpSTTProvider, NoOpTTSProvider
from lina.speech.service import SpeechService


class FakeSTTProvider:
    def __init__(
        self,
        error: Exception | None = None,
        text: str = "Merhaba Lina",
    ) -> None:
        self._error = error
        self._text = text
        self.call_count = 0
        self.state_reader = None
        self.observed_state = None

    def is_available(self) -> bool:
        return True

    def transcribe(self, recording: AudioRecordingResult) -> SpeechTranscriptionResult:
        self.call_count += 1
        if self.state_reader is not None:
            self.observed_state = self.state_reader()
        if self._error is not None:
            raise self._error
        return SpeechTranscriptionResult(
            text=self._text,
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


class FakeAudioRecorder:
    def __init__(self, error: Exception | None = None) -> None:
        self._error = error
        self.state_reader = None
        self.observed_state = None
        self.stop_count = 0

    def is_available(self) -> bool:
        return True

    def record_once(self) -> AudioRecordingResult:
        if self.state_reader is not None:
            self.observed_state = self.state_reader()
        if self._error is not None:
            raise self._error
        return AudioRecordingResult(
            audio_data=b"RIFFaudio",
            sample_rate=16000,
            channels=1,
            duration_seconds=1.0,
        )

    def stop(self) -> None:
        self.stop_count += 1


class BlockingAudioRecorder(FakeAudioRecorder):
    def __init__(self) -> None:
        super().__init__()
        self.started = threading.Event()
        self.stopped = threading.Event()

    def record_once(self) -> AudioRecordingResult:
        self.started.set()
        self.stopped.wait(timeout=2)
        return super().record_once()

    def stop(self) -> None:
        super().stop()
        self.stopped.set()


def _create_service(
    stt_provider=None,
    tts_provider=None,
    audio_recorder=None,
) -> SpeechService:
    return SpeechService(
        stt_provider=stt_provider or NoOpSTTProvider(),
        tts_provider=tts_provider or NoOpTTSProvider(),
        audio_recorder=audio_recorder,
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
    recorder = FakeAudioRecorder()
    service = _create_service(stt_provider=provider, audio_recorder=recorder)
    provider.state_reader = service.get_state
    recorder.state_reader = service.get_state

    result = service.transcribe_once()

    assert result.text == "Merhaba Lina"
    assert provider.call_count == 1
    assert recorder.observed_state is SpeechState.LISTENING
    assert provider.observed_state is SpeechState.TRANSCRIBING
    assert service.get_state() is SpeechState.IDLE


def test_transcribe_once_does_not_send_or_transform_text() -> None:
    service = _create_service(
        stt_provider=FakeSTTProvider(),
        audio_recorder=FakeAudioRecorder(),
    )

    result = service.transcribe_once()

    assert result == SpeechTranscriptionResult(
        text="Merhaba Lina",
        confidence=0.95,
        source="fake",
        is_final=True,
    )


def test_transcribe_once_preserves_empty_provider_result() -> None:
    service = _create_service(
        stt_provider=FakeSTTProvider(text=""),
        audio_recorder=FakeAudioRecorder(),
    )

    result = service.transcribe_once()

    assert result.text == ""
    assert result.is_final is True
    assert service.get_state() is SpeechState.IDLE


def test_provider_exception_does_not_leave_transcription_state_stuck() -> None:
    service = _create_service(
        stt_provider=FakeSTTProvider(RuntimeError("failure")),
        audio_recorder=FakeAudioRecorder(),
    )

    with pytest.raises(SpeechServiceError, match="transcription failed"):
        service.transcribe_once()

    assert service.get_state() is SpeechState.IDLE


def test_recorder_exception_does_not_leave_listening_state_stuck() -> None:
    service = _create_service(
        stt_provider=FakeSTTProvider(),
        audio_recorder=FakeAudioRecorder(SpeechServiceError("recording failed")),
    )

    with pytest.raises(SpeechServiceError, match="recording failed"):
        service.transcribe_once()

    assert service.get_state() is SpeechState.IDLE


def test_stop_listening_stops_active_recorder() -> None:
    recorder = BlockingAudioRecorder()
    service = _create_service(
        stt_provider=FakeSTTProvider(),
        audio_recorder=recorder,
    )
    thread = threading.Thread(target=service.transcribe_once)
    thread.start()
    assert recorder.started.wait(timeout=1)

    service.stop_listening()
    thread.join(timeout=1)

    assert recorder.stop_count == 1
    assert thread.is_alive() is False
    assert service.get_state() is SpeechState.IDLE


def test_duplicate_transcription_request_is_rejected() -> None:
    recorder = BlockingAudioRecorder()
    service = _create_service(
        stt_provider=FakeSTTProvider(),
        audio_recorder=recorder,
    )
    thread = threading.Thread(target=service.transcribe_once)
    thread.start()
    assert recorder.started.wait(timeout=1)

    with pytest.raises(SpeechServiceError, match="already active"):
        service.transcribe_once()

    service.stop_listening()
    thread.join(timeout=1)
    assert service.get_state() is SpeechState.IDLE


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


def test_shutdown_invalidates_inflight_transcription_and_late_state() -> None:
    recorder = BlockingAudioRecorder()
    service = _create_service(
        stt_provider=FakeSTTProvider(),
        audio_recorder=recorder,
    )
    states: list[SpeechState] = []
    errors: list[Exception] = []
    service.subscribe_state(states.append)

    def transcribe() -> None:
        try:
            service.transcribe_once()
        except Exception as error:
            errors.append(error)

    thread = threading.Thread(target=transcribe)
    thread.start()
    assert recorder.started.wait(timeout=1)
    service.shutdown()
    thread.join(timeout=1)

    assert thread.is_alive() is False
    assert errors and isinstance(errors[0], SpeechServiceError)
    assert service.get_state() is SpeechState.IDLE
    assert states == [SpeechState.LISTENING]
    assert service.is_stt_available() is False


def test_shutdown_is_idempotent() -> None:
    recorder = FakeAudioRecorder()
    service = _create_service(audio_recorder=recorder)
    service.shutdown()
    service.shutdown()
    assert recorder.stop_count == 1
    assert service.get_state() is SpeechState.IDLE
