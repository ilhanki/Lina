from __future__ import annotations

import threading

from lina.speech.models import SpeechNoInputError, SpeechServiceError, SpeechTranscriptionResult
from lina.voice.hands_free import HandsFreeConversationService


class FakeVoice:
    def __init__(self) -> None:
        self.wake_callback = None
        self.states = []
        self.finished = 0
        self.paused = 0
        self.resumed = 0

    def subscribe_wake_detected(self, callback):
        self.wake_callback = callback

    def begin_listening(self):
        self.states.append("command_listening")
        return True

    def begin_transcribing(self):
        self.states.append("transcribing")

    def begin_thinking(self):
        self.states.append("thinking")

    def finish_interaction(self):
        self.finished += 1

    def pause_hands_free(self):
        self.paused += 1
        return True

    def resume_hands_free(self):
        self.resumed += 1
        return True


class FakeSpeech:
    def __init__(self, result=None, error=None) -> None:
        self.result = result
        self.error = error
        self.stops = 0

    def transcribe_once(self):
        if self.error:
            raise self.error
        return self.result

    def stop_listening(self):
        self.stops += 1


def _result(text: str, confidence: float | None = 1.0):
    return SpeechTranscriptionResult(text, confidence, "fake", True, "tr", 1.2)


def test_wake_captures_transcribes_and_automatically_sends_command():
    voice = FakeVoice()
    service = HandsFreeConversationService(voice, FakeSpeech(_result("yarın spor hatırlat")))
    commands = []
    feedback = []
    completed = threading.Event()
    service.bind(lambda text: (commands.append(text), completed.set()), feedback.append)
    voice.wake_callback()
    assert completed.wait(1)
    assert feedback == ["Dinliyorum."]
    assert commands == ["yarın spor hatırlat"]
    assert voice.states == ["command_listening", "transcribing", "thinking"]
    assert service.metrics.wake_detection_count == 1
    assert service.metrics.false_wake_cancel_count == 0
    service.mark_response_completed()
    service.shutdown()


def test_empty_transcription_returns_safe_feedback_without_send():
    voice = FakeVoice()
    service = HandsFreeConversationService(voice, FakeSpeech(_result("  ")))
    feedback = []
    service.bind(lambda _text: None, feedback.append)
    voice.wake_callback()
    for _ in range(100):
        if voice.finished:
            break
        threading.Event().wait(0.005)
    assert feedback == ["Dinliyorum.", "Seni anlayamadım."]
    assert voice.finished == 1
    assert service.metrics.false_wake_cancel_count == 1


def test_low_confidence_requests_repeat():
    voice = FakeVoice()
    service = HandsFreeConversationService(voice, FakeSpeech(_result("belirsiz", 0.2)))
    feedback = []
    service.bind(lambda _text: None, feedback.append)
    voice.wake_callback()
    for _ in range(100):
        if voice.finished:
            break
        threading.Event().wait(0.005)
    assert feedback[-1] == "Tekrar söyler misin?"


def test_stt_failure_is_controlled_and_normal_flow_can_continue():
    voice = FakeVoice()
    service = HandsFreeConversationService(voice, FakeSpeech(error=SpeechServiceError("private")))
    feedback = []
    service.bind(lambda _text: None, feedback.append)
    voice.wake_callback()
    for _ in range(100):
        if voice.finished:
            break
        threading.Event().wait(0.005)
    assert feedback[-1] == "Mikrofona erişilemiyor."
    assert voice.finished == 1


def test_command_timeout_reports_no_audio():
    voice = FakeVoice()
    service = HandsFreeConversationService(voice, FakeSpeech(error=SpeechNoInputError("none")))
    feedback = []
    service.bind(lambda _text: None, feedback.append)
    voice.wake_callback()
    for _ in range(100):
        if voice.finished:
            break
        threading.Event().wait(0.005)
    assert feedback[-1] == "Bir şey duyamadım."


def test_pause_resume_cancel_and_shutdown_are_idempotent():
    voice = FakeVoice()
    speech = FakeSpeech(_result("test"))
    service = HandsFreeConversationService(voice, speech)
    assert service.pause()
    assert service.resume()
    service.cancel_active()
    service.shutdown()
    service.shutdown()
    assert voice.paused == 2
    assert voice.resumed == 1
    assert speech.stops == 3
