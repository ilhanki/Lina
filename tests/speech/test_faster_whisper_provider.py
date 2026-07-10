"""Tests for the local faster-whisper provider."""

from types import SimpleNamespace

import pytest

from lina.speech.faster_whisper_provider import FasterWhisperSTTProvider
from lina.speech.models import (
    AudioRecordingResult,
    SpeechTranscriptionError,
    SpeechUnavailableError,
)


class FakeWhisperModel:
    def __init__(self, segments=None, error: Exception | None = None) -> None:
        self._segments = segments or []
        self._error = error
        self.calls = []

    def transcribe(self, audio, **kwargs):
        self.calls.append((audio, kwargs))
        if self._error is not None:
            raise self._error
        return iter(self._segments), SimpleNamespace(language="tr")


class FakeModelFactory:
    def __init__(self, model=None, error: Exception | None = None) -> None:
        self.model = model or FakeWhisperModel()
        self.error = error
        self.calls = []

    def __call__(self, model_size: str, **kwargs):
        self.calls.append((model_size, kwargs))
        if self.error is not None:
            raise self.error
        return self.model


def _recording() -> AudioRecordingResult:
    return AudioRecordingResult(
        audio_data=b"RIFFfake-wave",
        sample_rate=16000,
        channels=1,
        duration_seconds=1.25,
    )


def _provider(factory: FakeModelFactory) -> FasterWhisperSTTProvider:
    return FasterWhisperSTTProvider(
        model_size="base",
        language="tr",
        device="cpu",
        compute_type="int8",
        model_factory=factory,
    )


def test_model_is_loaded_lazily_with_cpu_int8_configuration() -> None:
    factory = FakeModelFactory()
    provider = _provider(factory)

    assert factory.calls == []

    provider.transcribe(_recording())

    assert factory.calls == [("base", {"device": "cpu", "compute_type": "int8"})]


def test_model_is_created_only_once() -> None:
    factory = FakeModelFactory()
    provider = _provider(factory)

    provider.transcribe(_recording())
    provider.transcribe(_recording())

    assert len(factory.calls) == 1


def test_transcribe_uses_turkish_and_transcribe_task() -> None:
    model = FakeWhisperModel([SimpleNamespace(text=" Merhaba ")])
    provider = _provider(FakeModelFactory(model=model))

    result = provider.transcribe(_recording())

    _, arguments = model.calls[0]
    assert arguments == {"language": "tr", "task": "transcribe"}
    assert result.text == "Merhaba"
    assert result.language == "tr"
    assert result.source == "faster_whisper"
    assert result.duration_seconds == 1.25


def test_segment_text_is_joined_without_empty_segments() -> None:
    model = FakeWhisperModel(
        [
            SimpleNamespace(text=" Merhaba"),
            SimpleNamespace(text=" "),
            SimpleNamespace(text="Lina "),
        ]
    )
    provider = _provider(FakeModelFactory(model=model))

    result = provider.transcribe(_recording())

    assert result.text == "Merhaba Lina"


def test_empty_segments_return_empty_final_transcription() -> None:
    provider = _provider(
        FakeModelFactory(model=FakeWhisperModel([SimpleNamespace(text="  ")]))
    )

    result = provider.transcribe(_recording())

    assert result.text == ""
    assert result.is_final is True


def test_model_load_failure_becomes_unavailable_error() -> None:
    provider = _provider(FakeModelFactory(error=RuntimeError("download failed")))

    with pytest.raises(SpeechUnavailableError, match="could not be prepared"):
        provider.transcribe(_recording())


def test_transcription_failure_becomes_controlled_error() -> None:
    model = FakeWhisperModel(error=RuntimeError("decode failed"))
    provider = _provider(FakeModelFactory(model=model))

    with pytest.raises(SpeechTranscriptionError, match="transcription failed"):
        provider.transcribe(_recording())
