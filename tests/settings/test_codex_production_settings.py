from dataclasses import replace

import pytest

from lina.settings.models import CodexUserSettings, UserSettings


def test_v0131_codex_settings_migrate_with_safe_v0132_defaults() -> None:
    settings = UserSettings.from_dict({
        "schema_version": 10,
        "codex": {
            "bridge_enabled": True,
            "cli_executable_path": "C:/Tools/codex.cmd",
            "auto_detect_cli": False,
            "default_task_timeout_seconds": 600,
            "read_only_default": True,
        },
    })
    assert settings.schema_version == 11
    assert settings.codex.cli_executable_path == "C:/Tools/codex.cmd"
    assert settings.codex.resume_enabled
    assert settings.codex.diff_review_required
    assert settings.codex.diff_max_size_kb == 1024


def test_codex_production_settings_round_trip() -> None:
    raw = UserSettings(codex=CodexUserSettings(
        bridge_enabled=True, candidate_source="path:codex.cmd",
        session_retention_days=90, resume_enabled=False,
        diff_max_size_kb=2048, diagnostics_verbosity="detailed",
        last_cli_health_check="2026-07-19T10:00:00Z",
    )).to_dict()
    loaded = UserSettings.from_dict(raw)
    assert loaded.codex.candidate_source == "path:codex.cmd"
    assert loaded.codex.session_retention_days == 90
    assert not loaded.codex.resume_enabled
    assert loaded.codex.diff_max_size_kb == 2048
    assert loaded.codex.diagnostics_verbosity == "detailed"


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    (("session_retention_days", 14, 30),
     ("diff_max_size_kb", 99999, 1024),
     ("diagnostics_verbosity", "raw-secrets", "standard")),
)
def test_corrupt_codex_production_settings_fall_back(field: str, value, expected) -> None:
    settings = UserSettings.from_dict({"schema_version": 11, "codex": {field: value}})
    assert getattr(settings.codex, field) == expected


def test_diff_review_cannot_be_disabled_by_persisted_setting() -> None:
    settings = UserSettings.from_dict({
        "schema_version": 11, "codex": {"diff_review_required": False}
    })
    assert settings.codex.diff_review_required


def test_codex_health_metadata_is_bounded() -> None:
    settings = UserSettings.from_dict({
        "schema_version": 11,
        "codex": {"candidate_source": "x" * 500, "last_cli_health_check": "y" * 500},
    })
    assert len(settings.codex.candidate_source) == 80
    assert len(settings.codex.last_cli_health_check) == 80


@pytest.mark.parametrize(
    "changes",
    ({"diff_review_required": False}, {"session_retention_days": 14},
     {"diff_max_size_kb": 10}, {"diagnostics_verbosity": "raw"}),
)
def test_invalid_direct_codex_settings_are_rejected(changes: dict) -> None:
    with pytest.raises(ValueError):
        UserSettings(codex=replace(CodexUserSettings(), **changes))
