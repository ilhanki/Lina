from array import array

import pytest

from lina.speech.audio_processing import normalize_transcription, preprocess_pcm16, transcription_is_low_quality
from lina.speech.calibration import MicrophoneCalibrationService, MicrophoneLevel


def pcm(value, count=100):
    return array("h", [value] * count).tobytes()


def alternating(value, count=100):
    return array("h", [value if index % 2 else -value for index in range(count)]).tobytes()


def test_pcm_preprocessing_removes_dc_offset_and_bounds_clipping():
    source = array("h", [1000 + (-100 if index % 2 else 100) for index in range(100)]).tobytes()
    result = array("h")
    result.frombytes(preprocess_pcm16(source))
    assert abs(sum(result) / len(result)) <= 1
    assert max(abs(value) for value in result) <= 32767
    assert max(abs(value) for value in result) > 100


@pytest.mark.parametrize(("raw", "expected"), [
    ("  Merhaba   Lina  ", "Merhaba Lina"),
    ("[noise] Bugün nasılsın? [noise]", "Bugün nasılsın?"),
    ("hey, lina", "Hey Lina"),
    ("[silence]", ""),
])
def test_transcription_normalization(raw, expected):
    assert normalize_transcription(raw) == expected


def test_low_quality_uses_real_confidence_or_clear_empty_signal():
    assert transcription_is_low_quality("Merhaba", 0.2)
    assert transcription_is_low_quality("", None)
    assert not transcription_is_low_quality("Merhaba Lina", None)


def test_calibration_quiet_good_noisy_low_and_no_speech():
    service = MicrophoneCalibrationService()
    assert service.analyze(alternating(100), alternating(5000)).level is MicrophoneLevel.GOOD
    assert service.analyze(alternating(4000), alternating(6000)).level is MicrophoneLevel.NOISY
    assert service.analyze(alternating(50), alternating(500)).level is MicrophoneLevel.LOW
    assert service.analyze(alternating(100), alternating(100)).level is MicrophoneLevel.NO_SPEECH


def test_calibration_returns_bounded_threshold_without_audio_persistence():
    result = MicrophoneCalibrationService().analyze(alternating(300), alternating(4000))
    assert 0.006 <= result.suggested_threshold <= 0.25
    assert result.suggested_preset in {"sensitive", "balanced", "noisy"}
