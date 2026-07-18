from dataclasses import replace

import pytest

from lina.settings.models import UserSettings


def test_codex_security_controls_cannot_be_disabled():
    settings = UserSettings.from_dict({"codex": {
        "bridge_enabled": True,
        "approval_enforced": False,
        "workspace_restriction_enforced": False,
        "secret_filtering_enforced": False,
        "audit_logging_enforced": False,
        "privacy_mode": "full_prompts",
        "default_approval_behavior": "automatic",
    }})
    assert settings.codex.bridge_enabled is True
    assert settings.codex.approval_enforced is True
    assert settings.codex.workspace_restriction_enforced is True
    assert settings.codex.secret_filtering_enforced is True
    assert settings.codex.audit_logging_enforced is True
    assert settings.codex.privacy_mode == "metadata_only"
    assert settings.codex.default_approval_behavior == "always_ask"


def test_default_user_settings_are_turkish_and_local_first() -> None:
    settings = UserSettings()

    assert settings.general.language == "tr"
    assert settings.speech.auto_insert_transcription is True
    assert settings.system.close_behavior == "exit"
    assert settings.general.intent_routing_enabled is True
    assert settings.appearance.density == "comfortable"
    assert settings.appearance.right_panel_visible is True
    assert settings.appearance.right_panel_width == 320


def test_user_settings_round_trip_contains_only_known_preferences() -> None:
    settings = UserSettings()

    payload = settings.to_dict()

    assert UserSettings.from_dict(payload) == settings
    serialized = str(payload).casefold()
    assert "messages" not in serialized
    assert "image_bytes" not in serialized
    assert "base64" not in serialized
    assert payload["system"]["window_width"] == 1440
    assert payload["appearance"]["right_panel_section"] == "tools"


def test_invalid_values_fall_back_to_safe_defaults() -> None:
    settings = UserSettings.from_dict(
        {
            "schema_version": 1,
            "appearance": {"theme": "neon", "font_scale": 10, "density": "microscopic"},
            "models": {"text_model": "bad\nmodel"},
            "system": {"close_behavior": "shell"},
        }
    )

    assert settings.appearance.theme == "dark"
    assert settings.appearance.font_scale == 1.0
    assert settings.appearance.density == "comfortable"
    assert settings.models.text_model == "llama3.2:3b"
    assert settings.system.close_behavior == "exit"


def test_user_settings_are_immutable() -> None:
    with pytest.raises((AttributeError, TypeError)):
        UserSettings().appearance = replace(UserSettings().appearance, theme="light")
