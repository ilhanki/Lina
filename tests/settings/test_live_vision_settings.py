from lina.settings.models import UserSettings


def test_live_vision_defaults_and_round_trip():
    settings = UserSettings()
    assert settings.live_vision.enabled
    assert settings.live_vision.capture_interval_seconds == 2
    assert settings.live_vision.minimum_analysis_interval_seconds == 5
    assert settings.live_vision.monitor_duration_minutes == 5
    assert settings.live_vision.change_sensitivity == "medium"
    assert settings.live_vision.voice_live_vision_enabled
    assert settings.live_vision.realtime_camera_conversation_enabled
    assert settings.live_vision.automatic_camera_commentary_enabled
    assert settings.live_vision.mirror_camera_preview
    assert settings.live_vision.speak_semantic_changes
    assert settings.live_vision.commentary_cooldown_seconds == 10
    assert settings.live_vision.camera_analysis_interval_seconds == 3
    assert UserSettings.from_dict(settings.to_dict()) == settings


def test_schema_three_migrates_without_losing_values():
    settings = UserSettings.from_dict({"schema_version": 3, "vision": {"enabled": False}, "models": {"vision_model": "old-vl"}})
    assert not settings.vision.enabled
    assert settings.models.vision_model == "old-vl"
    assert settings.live_vision.enabled


def test_schema_four_migrates_camera_conversation_defaults_without_losing_values():
    settings = UserSettings.from_dict({
        "schema_version": 4,
        "live_vision": {"capture_interval_seconds": 1.0, "voice_live_vision_enabled": False},
    })
    assert settings.live_vision.capture_interval_seconds == 1.0
    assert not settings.live_vision.voice_live_vision_enabled
    assert settings.live_vision.realtime_camera_conversation_enabled
    assert settings.live_vision.commentary_cooldown_seconds == 10


def test_invalid_live_vision_values_fall_back_safely():
    settings = UserSettings.from_dict({"live_vision": {"default_source": "cloud", "change_sensitivity": "extreme", "capture_interval_seconds": 0}})
    assert settings.live_vision.default_source == "screen"
    assert settings.live_vision.change_sensitivity == "medium"
    assert settings.live_vision.capture_interval_seconds == 2
