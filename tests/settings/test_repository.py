import json

from lina.settings.models import UserSettings
from lina.settings.repository import UserSettingsRepository, default_user_settings_path


def test_missing_settings_file_returns_defaults(tmp_path) -> None:
    settings = UserSettingsRepository(tmp_path / "user-settings.json").load()

    assert settings == UserSettings()


def test_repository_round_trips_utf8_settings(tmp_path) -> None:
    repository = UserSettingsRepository(tmp_path / "user-settings.json")
    settings = UserSettings.from_dict({"general": {"language": "tr"}})

    repository.save(settings)

    assert repository.load() == settings
    assert json.loads(repository.file_path.read_text(encoding="utf-8"))["schema_version"] == 6


def test_malformed_settings_fall_back_without_deleting_file(tmp_path) -> None:
    path = tmp_path / "user-settings.json"
    path.write_text("{broken", encoding="utf-8")

    settings = UserSettingsRepository(path).load()

    assert settings == UserSettings()
    assert path.exists()


def test_future_schema_falls_back_without_overwriting_file(tmp_path) -> None:
    path = tmp_path / "user-settings.json"
    path.write_text(json.dumps({"schema_version": 999}), encoding="utf-8")

    assert UserSettingsRepository(path).load() == UserSettings()
    assert json.loads(path.read_text(encoding="utf-8"))["schema_version"] == 999


def test_default_path_is_outside_project_data(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "LocalAppData"))

    path = default_user_settings_path()

    assert path == tmp_path / "LocalAppData" / "Lina" / "user-settings.json"
