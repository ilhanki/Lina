"""Tests for speech capability models."""

from dataclasses import FrozenInstanceError

import pytest

from lina.speech.models import (
    SpeechState,
    SpeechSynthesisResult,
    SpeechTranscriptionResult,
)


def test_speech_state_defines_expected_lifecycle_values() -> None:
    assert set(SpeechState) == {
        SpeechState.IDLE,
        SpeechState.LISTENING,
        SpeechState.TRANSCRIBING,
        SpeechState.SPEAKING,
        SpeechState.ERROR,
        SpeechState.UNAVAILABLE,
    }


def test_speech_transcription_result_is_immutable() -> None:
    result = SpeechTranscriptionResult(
        text="Hello",
        confidence=0.9,
        source="fake",
        is_final=True,
    )

    assert result.text == "Hello"
    assert result.confidence == 0.9
    assert result.source == "fake"
    assert result.is_final is True

    with pytest.raises(FrozenInstanceError):
        result.text = "Changed"


def test_speech_synthesis_result_defaults_message_to_none() -> None:
    result = SpeechSynthesisResult(success=True)

    assert result.success is True
    assert result.message is None
