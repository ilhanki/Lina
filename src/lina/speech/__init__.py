"""Safe speech capability contracts and orchestration."""

from lina.speech.audio_processing import normalize_transcription, preprocess_pcm16, transcription_is_low_quality
from lina.speech.calibration import MicrophoneCalibrationResult, MicrophoneCalibrationService, MicrophoneLevel

__all__ = ["MicrophoneCalibrationResult", "MicrophoneCalibrationService", "MicrophoneLevel", "normalize_transcription", "preprocess_pcm16", "transcription_is_low_quality"]
