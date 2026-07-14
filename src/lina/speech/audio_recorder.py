"""Explicit, bounded, in-memory audio recording support."""

from __future__ import annotations

from collections.abc import Callable
from io import BytesIO
import threading
import logging
from typing import Any, Protocol
import wave

import sounddevice

from lina.speech.models import (
    AudioRecordingResult,
    SpeechRecordingError,
    SpeechNoInputError,
    SpeechUnavailableError,
)
from lina.voice.vad import VADResult, VoiceActivityDetector


_logger = logging.getLogger("lina.voice")


class AudioRecorder(Protocol):
    """Contract for explicit single-request audio capture."""

    def is_available(self) -> bool:
        """Return whether an input device is available."""

    def record_once(self) -> AudioRecordingResult:
        """Capture one bounded recording initiated by the user."""

    def stop(self) -> None:
        """Stop the active recording, if any."""


class NoOpAudioRecorder:
    """Safe recorder used when microphone access is disabled."""

    def is_available(self) -> bool:
        return False

    def record_once(self) -> AudioRecordingResult:
        raise SpeechUnavailableError("Audio recorder is unavailable")

    def stop(self) -> None:
        return None


class SoundDeviceAudioRecorder:
    """Capture one mono PCM recording through sounddevice without persistence."""

    def __init__(
        self,
        sample_rate: int,
        channels: int,
        max_recording_seconds: float,
        silence_threshold: float,
        silence_duration_seconds: float,
        backend: Any = sounddevice,
        device_id: int | None = None,
    ) -> None:
        self._sample_rate = sample_rate
        self._channels = channels
        self._max_recording_seconds = max_recording_seconds
        self._silence_threshold = silence_threshold
        self._silence_duration_seconds = silence_duration_seconds
        self._backend = backend
        self._device_id = device_id
        self._stop_event = threading.Event()
        self._recording_lock = threading.Lock()
        self._is_recording = False

    def is_available(self) -> bool:
        try:
            device_id = self._resolve_device()
            device = self._backend.query_devices(device_id) if device_id is not None else self._backend.query_devices(kind="input")
        except Exception:
            return False
        return int(device.get("max_input_channels", 0)) >= self._channels

    def set_device(self, device_id: int | None) -> None:
        self._device_id = device_id

    def record_once(self) -> AudioRecordingResult:
        with self._recording_lock:
            if self._is_recording:
                raise SpeechRecordingError("Audio recording is already active")
            self._is_recording = True

        self._stop_event.clear()
        chunks: list[bytes] = []
        recorded_frames = 0
        callback_error: Exception | None = None
        vad_result: VADResult | None = None
        vad = VoiceActivityDetector(
            sample_rate=self._sample_rate,
            channels=self._channels,
            noise_threshold=self._silence_threshold,
            silence_timeout=self._silence_duration_seconds,
            minimum_speech_duration=0.25,
            maximum_duration=self._max_recording_seconds,
            no_speech_timeout=min(5.0, self._max_recording_seconds),
        )

        def capture(indata, frames, time_info, status) -> None:
            nonlocal recorded_frames, callback_error, vad_result
            if status:
                callback_error = SpeechRecordingError("Audio input stream reported an error")
                self._stop_event.set()
                return

            chunk = indata.tobytes()
            chunks.append(chunk)
            recorded_frames += frames
            vad_result = vad.feed(chunk)
            if vad_result is not None:
                self._stop_event.set()

        try:
            self._capture_stream(capture)
            if callback_error is not None:
                raise callback_error
            if not chunks:
                raise SpeechRecordingError("Audio recording produced no data")
            if vad_result is not None and not vad_result.accepted:
                raise SpeechNoInputError("No valid speech was detected")
            pcm_data = vad_result.pcm_data if vad_result is not None else b"".join(chunks)
            audio_data = _build_wav(
                pcm_data=pcm_data,
                sample_rate=self._sample_rate,
                channels=self._channels,
            )
            return AudioRecordingResult(
                audio_data=audio_data,
                sample_rate=self._sample_rate,
                channels=self._channels,
                duration_seconds=recorded_frames / self._sample_rate,
            )
        except SpeechRecordingError:
            raise
        except Exception as error:
            raise SpeechRecordingError("Audio recording failed") from error
        finally:
            with self._recording_lock:
                self._is_recording = False
            self._stop_event.clear()

    def stop(self) -> None:
        self._stop_event.set()

    def _capture_stream(self, callback: Callable[..., None]) -> None:
        timeout = self._max_recording_seconds + 1.0
        with self._backend.InputStream(
            samplerate=self._sample_rate,
            channels=self._channels,
            dtype="int16",
            device=self._resolve_device(),
            callback=callback,
        ):
            if not self._stop_event.wait(timeout):
                raise SpeechRecordingError("Audio recording did not stop in time")

    def _resolve_device(self) -> int | None:
        if self._device_id is None:
            return None
        try:
            device = self._backend.query_devices(self._device_id)
            if int(device.get("max_input_channels", 0)) >= self._channels:
                return self._device_id
        except Exception:
            pass
        _logger.warning("audio_input_fallback reason=selected_device_unavailable")
        return None


def _build_wav(pcm_data: bytes, sample_rate: int, channels: int) -> bytes:
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)
    return buffer.getvalue()
