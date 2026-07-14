"""Small in-memory PCM voice activity detector for bounded local capture."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class VADEndReason(str, Enum):
    SPEECH_END = "speech_end"
    SHORT_NOISE = "short_noise"
    NO_SPEECH = "no_speech"
    MAX_DURATION = "max_duration"


@dataclass(frozen=True, slots=True)
class VADResult:
    pcm_data: bytes
    duration_seconds: float
    speech_seconds: float
    accepted: bool
    reason: VADEndReason


class VoiceActivityDetector:
    """Detect one utterance using peak energy and bounded PCM buffers."""

    def __init__(
        self,
        *,
        sample_rate: int,
        channels: int = 1,
        noise_threshold: float = 0.015,
        silence_timeout: float = 1.0,
        minimum_speech_duration: float = 0.25,
        maximum_duration: float = 25.0,
        no_speech_timeout: float = 5.0,
    ) -> None:
        if sample_rate <= 0 or channels <= 0:
            raise ValueError("Sample rate and channels must be positive")
        if not 0.0 <= noise_threshold <= 1.0:
            raise ValueError("Noise threshold must be between zero and one")
        if min(silence_timeout, minimum_speech_duration, maximum_duration, no_speech_timeout) <= 0:
            raise ValueError("VAD durations must be positive")
        self.sample_rate = sample_rate
        self.channels = channels
        self.noise_threshold = noise_threshold
        self.silence_timeout = silence_timeout
        self.minimum_speech_duration = minimum_speech_duration
        self.maximum_duration = maximum_duration
        self.no_speech_timeout = no_speech_timeout
        self.reset()

    def reset(self) -> None:
        self._chunks: list[bytes] = []
        self._total_seconds = 0.0
        self._speech_seconds = 0.0
        self._trailing_silence = 0.0
        self._speech_started = False
        self._completed = False

    def feed(self, pcm_data: bytes) -> VADResult | None:
        if self._completed:
            return None
        frame_width = 2 * self.channels
        if not pcm_data or len(pcm_data) % frame_width:
            raise ValueError("PCM data must contain complete signed 16-bit frames")
        duration = len(pcm_data) / frame_width / self.sample_rate
        self._total_seconds += duration
        voiced = _pcm_peak(pcm_data) >= self.noise_threshold

        if voiced:
            self._speech_started = True
            self._speech_seconds += duration
            self._trailing_silence = 0.0
            self._chunks.append(pcm_data)
        elif self._speech_started:
            self._trailing_silence += duration
            self._chunks.append(pcm_data)

        if self._total_seconds >= self.maximum_duration:
            return self._finish(VADEndReason.MAX_DURATION)
        if not self._speech_started and self._total_seconds >= self.no_speech_timeout:
            return self._finish(VADEndReason.NO_SPEECH)
        if self._speech_started and self._trailing_silence >= self.silence_timeout:
            reason = VADEndReason.SPEECH_END if self._speech_seconds >= self.minimum_speech_duration else VADEndReason.SHORT_NOISE
            return self._finish(reason)
        return None

    def _finish(self, reason: VADEndReason) -> VADResult:
        self._completed = True
        accepted = self._speech_seconds >= self.minimum_speech_duration and reason in {VADEndReason.SPEECH_END, VADEndReason.MAX_DURATION}
        return VADResult(
            pcm_data=b"".join(self._chunks) if accepted else b"",
            duration_seconds=self._total_seconds,
            speech_seconds=self._speech_seconds,
            accepted=accepted,
            reason=reason,
        )


def _pcm_peak(pcm_data: bytes) -> float:
    samples = memoryview(pcm_data).cast("h")
    peak = max((abs(sample) for sample in samples), default=0)
    return peak / 32768.0
