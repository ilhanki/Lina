"""Privacy-safe microphone calibration from ephemeral PCM measurements."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math


class MicrophoneLevel(str, Enum):
    LOW = "low"
    GOOD = "good"
    NOISY = "noisy"
    NO_SPEECH = "no_speech"


@dataclass(frozen=True, slots=True)
class MicrophoneCalibrationResult:
    level: MicrophoneLevel
    suggested_threshold: float
    suggested_preset: str
    noise_rms: float
    speech_rms: float
    message: str


class MicrophoneCalibrationService:
    def analyze(self, noise_pcm: bytes, speech_pcm: bytes) -> MicrophoneCalibrationResult:
        noise = _rms(noise_pcm)
        speech = _rms(speech_pcm)
        threshold = max(0.006, min(0.25, noise * 2.8 + 0.004))
        if noise >= 0.08 and speech > noise * 1.15:
            level, preset, message = MicrophoneLevel.NOISY, "noisy", "Ortam gürültüsü konuşmayı bastırıyor."
        elif speech < max(0.008, noise * 1.6):
            level, preset, message = MicrophoneLevel.NO_SPEECH, "balanced", "Konuşma algılanamadı."
        elif speech / max(noise, 0.001) < 2.0:
            level, preset, message = MicrophoneLevel.NOISY, "noisy", "Ortam gürültüsü konuşmayı bastırıyor."
        elif speech < 0.04:
            level, preset, message = MicrophoneLevel.LOW, "sensitive", "Mikrofon seviyesi çok düşük görünüyor."
        else:
            level, preset, message = MicrophoneLevel.GOOD, "balanced", "Mikrofon seviyesi iyi."
        return MicrophoneCalibrationResult(level, round(threshold, 4), preset, round(noise, 4), round(speech, 4), message)


def _rms(pcm: bytes) -> float:
    if not pcm or len(pcm) % 2:
        return 0.0
    samples = memoryview(pcm).cast("h")
    return math.sqrt(sum((sample / 32768.0) ** 2 for sample in samples) / max(1, len(samples)))
