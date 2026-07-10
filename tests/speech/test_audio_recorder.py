"""Tests for bounded in-memory audio recording."""

from array import array
import wave
from io import BytesIO

import pytest

from lina.speech.audio_recorder import NoOpAudioRecorder, SoundDeviceAudioRecorder
from lina.speech.models import SpeechRecordingError, SpeechUnavailableError


class FakeInputStream:
    def __init__(self, backend, callback) -> None:
        self._backend = backend
        self._callback = callback

    def __enter__(self):
        if self._backend.stream_error is not None:
            raise self._backend.stream_error
        for chunk, frames, status in self._backend.chunks:
            self._callback(chunk, frames, None, status)
        if self._backend.after_chunks is not None:
            self._backend.after_chunks()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        return None


class FakeSoundDevice:
    def __init__(self, chunks=None, stream_error: Exception | None = None) -> None:
        self.chunks = chunks or []
        self.stream_error = stream_error
        self.input_stream_arguments = None
        self.device = {"max_input_channels": 1}
        self.after_chunks = None

    def query_devices(self, kind: str):
        assert kind == "input"
        return self.device

    def InputStream(self, **kwargs):
        self.input_stream_arguments = kwargs
        return FakeInputStream(self, kwargs["callback"])


def _audio_chunk(value: int, frame_count: int) -> array:
    return array("h", [value] * frame_count)


def _create_recorder(backend: FakeSoundDevice) -> SoundDeviceAudioRecorder:
    return SoundDeviceAudioRecorder(
        sample_rate=100,
        channels=1,
        max_recording_seconds=1.0,
        silence_threshold=0.015,
        silence_duration_seconds=0.2,
        backend=backend,
    )


def test_noop_audio_recorder_is_unavailable() -> None:
    recorder = NoOpAudioRecorder()

    assert recorder.is_available() is False
    with pytest.raises(SpeechUnavailableError):
        recorder.record_once()


def test_sounddevice_recorder_reports_input_device_availability() -> None:
    backend = FakeSoundDevice()
    recorder = _create_recorder(backend)

    assert recorder.is_available() is True


def test_record_once_returns_bounded_in_memory_wav() -> None:
    backend = FakeSoundDevice(
        chunks=[(_audio_chunk(2000, 100), 100, False)],
    )
    recorder = _create_recorder(backend)

    result = recorder.record_once()

    assert result.sample_rate == 100
    assert result.channels == 1
    assert result.duration_seconds == 1.0
    assert result.audio_data.startswith(b"RIFF")
    with wave.open(BytesIO(result.audio_data), "rb") as wav_file:
        assert wav_file.getframerate() == 100
        assert wav_file.getnchannels() == 1
    assert backend.input_stream_arguments["dtype"] == "int16"


def test_record_once_stops_after_configured_silence() -> None:
    backend = FakeSoundDevice(
        chunks=[
            (_audio_chunk(0, 10), 10, False),
            (_audio_chunk(0, 10), 10, False),
        ],
    )
    recorder = _create_recorder(backend)

    result = recorder.record_once()

    assert result.duration_seconds == 0.2


def test_stream_failure_becomes_controlled_recording_error() -> None:
    recorder = _create_recorder(FakeSoundDevice(stream_error=RuntimeError("device error")))

    with pytest.raises(SpeechRecordingError, match="Audio recording failed"):
        recorder.record_once()


def test_stream_status_becomes_controlled_recording_error() -> None:
    backend = FakeSoundDevice(chunks=[(_audio_chunk(0, 10), 10, "overflow")])
    recorder = _create_recorder(backend)

    with pytest.raises(SpeechRecordingError, match="reported an error"):
        recorder.record_once()


def test_stop_ends_an_active_recording() -> None:
    backend = FakeSoundDevice(chunks=[(_audio_chunk(2000, 10), 10, False)])
    recorder = _create_recorder(backend)
    backend.after_chunks = recorder.stop

    result = recorder.record_once()

    assert result.duration_seconds == 0.1
