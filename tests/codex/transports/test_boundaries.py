from pathlib import Path

from lina.settings.models import UserSettings


TRANSPORT_ROOT = Path(__file__).parents[3] / "src" / "lina" / "codex" / "transports"


def test_transport_never_uses_shell_true_or_reads_auth_cache() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in TRANSPORT_ROOT.glob("*.py"))
    assert "shell=True" not in source
    assert "auth.json" not in source.casefold()


def test_new_codex_settings_round_trip_without_disabling_safety() -> None:
    settings = UserSettings.from_dict({"codex": {
        "cli_executable_path": "C:/Tools/codex.exe",
        "auto_detect_cli": False,
        "default_task_timeout_seconds": 180,
        "read_only_default": True,
        "modification_confirmation": False,
    }})
    assert settings.codex.cli_executable_path == "C:/Tools/codex.exe"
    assert not settings.codex.auto_detect_cli
    assert settings.codex.default_task_timeout_seconds == 180
    assert settings.codex.modification_confirmation
    assert settings.to_dict()["codex"]["modification_confirmation"] is True
