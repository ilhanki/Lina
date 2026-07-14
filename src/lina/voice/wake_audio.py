"""Energy-gated sounddevice source for local wake-word STT."""

from __future__ import annotations

from collections.abc import Iterator
import queue
import threading
from typing import Any

import sounddevice

from lina.speech.audio_devices import AudioInputDeviceService
from lina.speech.audio_recorder import _build_wav
from lina.speech.models import AudioRecordingResult, SpeechRecordingError
from lina.voice.vad import VoiceActivityDetector


class SoundDeviceWakeAudioSource:
    """Yield only bounded speech segments; silence never invokes full STT."""

    def __init__(
        self,
        *,
        sample_rate: int,
        channels: int,
        noise_threshold: float,
        device_id: int | None = None,
        backend: Any = sounddevice,
        silence_timeout: float = 0.8,
        minimum_speech_duration: float = 0.2,
        maximum_utterance_duration: float = 3.5,
    ) -> None:
        self._sample_rate = sample_rate
        self._channels = channels
        self._noise_threshold = noise_threshold
        self._device_id = device_id
        self._backend = backend
        self._silence_timeout = silence_timeout
        self._minimum_speech_duration = minimum_speech_duration
        self._maximum_utterance_duration = maximum_utterance_duration
        self._devices = AudioInputDeviceService(backend)

    def is_available(self) -> bool:
        return self._devices.is_available(self._device_id)

    def set_device(self, device_id: int | None) -> None:
        self._device_id = device_id

    def __call__(self, stop_event: threading.Event) -> Iterator[AudioRecordingResult]:
        device_id = self._devices.resolve(self._device_id)
        if device_id is None:
            raise SpeechRecordingError("Microphone input is unavailable")
        completed: queue.Queue[AudioRecordingResult] = queue.Queue(maxsize=2)
        detector = self._new_vad()

        def capture(indata, _frames, _time_info, status) -> None:
            nonlocal detector
            if status or stop_event.is_set():
                return
            result = detector.feed(indata.tobytes())
            if result is None:
                return
            detector = self._new_vad()
            if not result.accepted:
                return
            recording = AudioRecordingResult(
                audio_data=_build_wav(result.pcm_data, self._sample_rate, self._channels),
                sample_rate=self._sample_rate,
                channels=self._channels,
                duration_seconds=result.duration_seconds,
            )
            try:
                completed.put_nowait(recording)
            except queue.Full:
                return

        with self._backend.InputStream(
            samplerate=self._sample_rate,
            channels=self._channels,
            dtype="int16",
            device=device_id,
            callback=capture,
        ):
            while not stop_event.is_set():
                try:
                    yield completed.get(timeout=0.1)
                except queue.Empty:
                    continue

    def _new_vad(self) -> VoiceActivityDetector:
        return VoiceActivityDetector(
            sample_rate=self._sample_rate,
            channels=self._channels,
            noise_threshold=self._noise_threshold,
            silence_timeout=self._silence_timeout,
            minimum_speech_duration=self._minimum_speech_duration,
            maximum_duration=self._maximum_utterance_duration,
            no_speech_timeout=self._maximum_utterance_duration,
        )
