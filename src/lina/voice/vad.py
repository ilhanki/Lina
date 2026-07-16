"""Small in-memory PCM voice activity detector for bounded local capture."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from collections import deque


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
        pre_roll_seconds: float = 0.18,
        adaptive_noise: bool = True,
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
        self.pre_roll_seconds = max(0.0, min(pre_roll_seconds, 0.5))
        self.adaptive_noise = adaptive_noise
        self.reset()

    def reset(self) -> None:
        self._chunks: list[bytes] = []
        self._total_seconds = 0.0
        self._speech_seconds = 0.0
        self._trailing_silence = 0.0
        self._speech_started = False
        self._completed = False
        self._pre_roll: deque[tuple[bytes, float]] = deque()
        self._pre_roll_duration = 0.0
        self._noise_floor = 0.0

    def feed(self, pcm_data: bytes) -> VADResult | None:
        if self._completed:
            return None
        frame_width = 2 * self.channels
        if not pcm_data or len(pcm_data) % frame_width:
            raise ValueError("PCM data must contain complete signed 16-bit frames")
        duration = len(pcm_data) / frame_width / self.sample_rate
        self._total_seconds += duration
        peak = _pcm_peak(pcm_data)
        effective_threshold = max(self.noise_threshold, self._noise_floor * 2.6) if self.adaptive_noise else self.noise_threshold
        voiced = peak >= effective_threshold

        if voiced:
            if not self._speech_started and self._pre_roll:
                self._chunks.extend(chunk for chunk, _duration in self._pre_roll)
                self._pre_roll.clear()
                self._pre_roll_duration = 0.0
            self._speech_started = True
            self._speech_seconds += duration
            self._trailing_silence = 0.0
            self._chunks.append(pcm_data)
        elif self._speech_started:
            self._trailing_silence += duration
            self._chunks.append(pcm_data)
        else:
            if self.adaptive_noise:
                self._noise_floor = peak if self._noise_floor == 0.0 else self._noise_floor * 0.9 + peak * 0.1
            if self.pre_roll_seconds:
                self._pre_roll.append((pcm_data, duration))
                self._pre_roll_duration += duration
                while self._pre_roll and self._pre_roll_duration - self._pre_roll[0][1] >= self.pre_roll_seconds:
                    _old, old_duration = self._pre_roll.popleft()
                    self._pre_roll_duration -= old_duration

        if self._total_seconds + 1e-9 >= self.maximum_duration:
            return self._finish(VADEndReason.MAX_DURATION)
        if not self._speech_started and self._total_seconds + 1e-9 >= self.no_speech_timeout:
            return self._finish(VADEndReason.NO_SPEECH)
        if self._speech_started and self._trailing_silence + 1e-9 >= self.silence_timeout:
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
