from __future__ import annotations

import json

from lina.settings.models import SCHEMA_VERSION, UserSettings
from lina.settings.repository import UserSettingsRepository


def test_voice_and_performance_defaults_are_privacy_safe():
    settings = UserSettings()
    assert not settings.speech.voice_responses_enabled
    assert settings.speech.transcription_mode == "insert"
    assert settings.speech.barge_in_enabled
    assert not settings.speech.wake_word_enabled
    assert settings.speech.wake_phrase == "Hey Lina"
    assert settings.models.keep_alive == "5m"
    assert settings.models.max_output_tokens == 512
    assert not settings.models.warm_up_enabled


def test_schema_one_migrates_without_losing_old_values():
    settings = UserSettings.from_dict({
        "schema_version": 1,
        "appearance": {"theme": "light", "font_scale": 1.2},
        "models": {"text_model": "old-text", "vision_model": "old-vision"},
        "speech": {"enabled": False, "language": "tr", "auto_insert_transcription": False},
    })
    assert settings.schema_version == SCHEMA_VERSION == 5
    assert settings.appearance.theme == "light"
    assert settings.models.text_model == "old-text"
    assert not settings.speech.enabled
    assert settings.speech.transcription_mode == "send"


def test_invalid_voice_and_model_tuning_values_fall_back():
    settings = UserSettings.from_dict({
        "speech": {"speech_rate": 99, "volume": -1, "transcription_mode": "always"},
        "models": {"keep_alive": "forever", "max_output_tokens": 1, "context_budget": 1},
    })
    assert settings.speech.speech_rate == 1.0
    assert settings.speech.volume == 1.0
    assert settings.speech.transcription_mode == "insert"
    assert settings.models.keep_alive == "5m"
    assert settings.models.max_output_tokens == 512
    assert settings.models.context_budget == 12000


def test_unknown_system_voice_is_preserved_for_runtime_fallback():
    settings = UserSettings.from_dict({"speech": {"system_voice": "missing-id"}})
    assert settings.speech.system_voice == "missing-id"


def test_new_settings_restart_persistence(tmp_path):
    path = tmp_path / "user-settings.json"
    repository = UserSettingsRepository(path)
    raw = UserSettings().to_dict()
    raw["speech"].update({"voice_responses_enabled": True, "volume": 0.4})
    raw["models"].update({"keep_alive": "15m", "warm_up_enabled": True})
    settings = UserSettings.from_dict(raw)
    repository.save(settings)
    loaded = repository.load()
    assert loaded == settings
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 5
    assert payload["speech"]["voice_responses_enabled"] is True
    assert payload["models"]["keep_alive"] == "15m"


def test_hands_free_defaults_are_private_and_opt_in():
    speech = UserSettings().speech
    assert not speech.hands_free_enabled
    assert not speech.wake_word_enabled
    assert speech.wake_phrase == "Hey Lina"
    assert speech.wake_word_indicator_enabled
    assert speech.return_to_wake_listening
    assert speech.voice_confirmation_enabled
    assert speech.barge_in_enabled
    assert speech.microphone_device_id is None


def test_schema_two_migrates_and_preserves_voice_values():
    settings = UserSettings.from_dict(
        {
            "schema_version": 2,
            "speech": {
                "enabled": False,
                "voice_responses_enabled": True,
                "wake_phrase": "Hey Asistan",
                "volume": 0.4,
            },
        }
    )
    assert settings.schema_version == 5
    assert not settings.speech.enabled
    assert settings.speech.voice_responses_enabled
    assert settings.speech.wake_phrase == "Hey Asistan"
    assert settings.speech.volume == 0.4
    assert not settings.speech.hands_free_enabled


def test_invalid_wake_phrase_safely_falls_back():
    settings = UserSettings.from_dict({"speech": {"wake_phrase": "Lina"}})
    assert settings.speech.wake_phrase == "Hey Lina"


def test_hands_free_settings_restart_persistence(tmp_path):
    path = tmp_path / "user-settings.json"
    repository = UserSettingsRepository(path)
    raw = UserSettings().to_dict()
    raw["speech"].update(
        {
            "hands_free_enabled": True,
            "wake_word_enabled": True,
            "return_to_wake_listening": False,
            "voice_confirmation_enabled": False,
            "microphone_device_id": 3,
        }
    )
    repository.save(UserSettings.from_dict(raw))
    loaded = repository.load().speech
    assert loaded.hands_free_enabled
    assert loaded.wake_word_enabled
    assert not loaded.return_to_wake_listening
    assert not loaded.voice_confirmation_enabled
    assert loaded.microphone_device_id == 3
