from array import array
from io import BytesIO
import threading
import wave

import pytest

from lina.voice.wake_audio import SoundDeviceWakeAudioSource


class Default:
    device = (0, 1)


class FakeInputStream:
    def __init__(self, backend, callback):
        self.backend = backend
        self.callback = callback

    def __enter__(self):
        for chunk in self.backend.chunks:
            self.callback(chunk, len(chunk), None, False)
        return self

    def __exit__(self, *_args):
        return None


class FakeBackend:
    default = Default()

    def __init__(self, chunks):
        self.chunks = chunks
        self.arguments = None
        self.devices = [{"name": "Mic", "max_input_channels": 1}]

    def query_devices(self, device=None, kind=None):
        if device is not None:
            return self.devices[device]
        if kind == "input":
            return self.devices[0]
        return self.devices

    def InputStream(self, **kwargs):
        self.arguments = kwargs
        return FakeInputStream(self, kwargs["callback"])


def _chunk(value, frames=10):
    return array("h", [value] * frames)


def test_energy_gated_source_yields_bounded_wav_only_after_valid_speech():
    backend = FakeBackend(
        [_chunk(1000), _chunk(0), _chunk(0), _chunk(10000), _chunk(10000), _chunk(0), _chunk(0)]
    )
    source = SoundDeviceWakeAudioSource(
        sample_rate=100,
        channels=1,
        noise_threshold=0.1,
        silence_timeout=0.2,
        minimum_speech_duration=0.2,
        backend=backend,
    )
    stop = threading.Event()
    iterator = source(stop)
    recording = next(iterator)
    stop.set()
    with pytest.raises(StopIteration):
        next(iterator)
    assert recording.audio_data.startswith(b"RIFF")
    with wave.open(BytesIO(recording.audio_data), "rb") as wav:
        assert wav.getframerate() == 100
        assert wav.getnchannels() == 1
    assert backend.arguments["device"] == 0
    assert backend.arguments["dtype"] == "int16"


def test_source_reports_unavailable_without_input_device():
    backend = FakeBackend([])
    backend.devices = []
    source = SoundDeviceWakeAudioSource(
        sample_rate=100,
        channels=1,
        noise_threshold=0.1,
        backend=backend,
    )
    assert not source.is_available()
