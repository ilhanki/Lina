from array import array

import pytest

from lina.voice.vad import VADEndReason, VoiceActivityDetector


def _pcm(value: int, frames: int) -> bytes:
    return array("h", [value] * frames).tobytes()


def _vad(**overrides) -> VoiceActivityDetector:
    settings = dict(
        sample_rate=100,
        noise_threshold=0.1,
        silence_timeout=0.2,
        minimum_speech_duration=0.2,
        maximum_duration=1.0,
        no_speech_timeout=0.4,
    )
    settings.update(overrides)
    return VoiceActivityDetector(**settings)


def test_vad_silence_only_times_out_without_audio():
    vad = _vad()
    assert vad.feed(_pcm(0, 20)) is None
    result = vad.feed(_pcm(0, 20))
    assert result.reason is VADEndReason.NO_SPEECH
    assert not result.accepted
    assert result.pcm_data == b""


def test_vad_short_noise_is_rejected():
    vad = _vad()
    assert vad.feed(_pcm(10000, 10)) is None
    result = vad.feed(_pcm(0, 20))
    assert result.reason is VADEndReason.SHORT_NOISE
    assert not result.accepted


def test_vad_detects_speech_start_and_silence_end():
    vad = _vad()
    assert vad.feed(_pcm(10000, 20)) is None
    result = vad.feed(_pcm(0, 20))
    assert result.reason is VADEndReason.SPEECH_END
    assert result.accepted
    assert result.speech_seconds == pytest.approx(0.2)
    assert result.pcm_data


def test_vad_stops_at_maximum_duration():
    vad = _vad(maximum_duration=0.3)
    assert vad.feed(_pcm(10000, 20)) is None
    result = vad.feed(_pcm(10000, 10))
    assert result.reason is VADEndReason.MAX_DURATION
    assert result.accepted


def test_vad_noise_threshold_is_respected():
    vad = _vad(noise_threshold=0.5)
    result = vad.feed(_pcm(1000, 40))
    assert result.reason is VADEndReason.NO_SPEECH


def test_vad_rejects_incomplete_pcm_frames():
    with pytest.raises(ValueError):
        _vad().feed(b"\x00")


def test_vad_reset_allows_new_utterance():
    vad = _vad()
    vad.feed(_pcm(0, 40))
    vad.reset()
    assert vad.feed(_pcm(10000, 20)) is None
    assert vad.feed(_pcm(0, 20)).accepted
