from __future__ import annotations

import threading

import pytest

from lina.speech.models import AudioRecordingResult, SpeechTranscriptionResult
from lina.voice.wake_word import (
    STTWakeWordDetector,
    UnavailableWakeWordDetector,
    normalize_wake_phrase,
    validate_wake_phrase,
    wake_phrase_matches,
)


class FakeSTT:
    def __init__(self, texts: list[str], available: bool = True) -> None:
        self.texts = texts
        self.available = available
        self.calls = 0

    def is_available(self) -> bool:
        return self.available

    def transcribe(self, _recording):
        text = self.texts[self.calls]
        self.calls += 1
        return SpeechTranscriptionResult(text, 1.0, "fake", True, "tr", 0.5)


def _recording() -> AudioRecordingResult:
    return AudioRecordingResult(b"RIFF", 16000, 1, 0.5)


@pytest.mark.parametrize("value", ["Hey Lina", "hey lina", "HEY, LINA!", "  hey   lina "])
def test_wake_phrase_normalization(value):
    assert normalize_wake_phrase(value) == "hey lina"


@pytest.mark.parametrize("value", ["hey lina", "he lina", "Hey, Lina!"])
def test_supported_wake_phrase_variants(value):
    assert wake_phrase_matches(value)


@pytest.mark.parametrize("value", ["lina", "hey", "hey linaya", "hey lina nasılsın", "şey lina"])
def test_wake_phrase_rejects_false_positives(value):
    assert not wake_phrase_matches(value)


def test_invalid_wake_phrase_is_rejected():
    with pytest.raises(ValueError):
        validate_wake_phrase("Lina")


def test_unavailable_detector_is_safe_and_never_runs():
    detector = UnavailableWakeWordDetector()
    assert not detector.is_available()
    assert not detector.start()
    assert not detector.is_running()
    detector.stop()
    detector.shutdown()


def test_stt_detector_start_duplicate_start_detect_stop_and_shutdown():
    release = threading.Event()

    def source(stop_event):
        yield _recording()
        release.wait(1)
        stop_event.set()

    detected = threading.Event()
    provider = FakeSTT(["Hey, Lina!"])
    detector = STTWakeWordDetector(provider, source)
    assert detector.start(detected.set)
    assert detector.start(detected.set)
    assert detected.wait(1)
    assert provider.calls == 1
    release.set()
    detector.stop()
    assert not detector.is_running()
    detector.shutdown()
    assert not detector.start()


def test_detector_does_not_callback_for_unmatched_transcription():
    def source(stop_event):
        yield _recording()
        stop_event.set()

    detected = threading.Event()
    detector = STTWakeWordDetector(FakeSTT(["Merhaba dünya"]), source)
    assert detector.start(detected.set)
    detector.stop()
    assert not detected.is_set()


def test_detector_reports_unavailable_stt():
    detector = STTWakeWordDetector(FakeSTT([], available=False), lambda _stop: ())
    assert not detector.is_available()
    assert not detector.start()
