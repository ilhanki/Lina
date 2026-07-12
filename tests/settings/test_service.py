from dataclasses import replace

from lina.settings.models import UserSettings
from lina.settings.repository import UserSettingsRepository
from lina.settings.service import UserSettingsService


def test_service_loads_current_settings_and_notifies_on_change(tmp_path) -> None:
    service = UserSettingsService(UserSettingsRepository(tmp_path / "settings.json"))
    changes: list[UserSettings] = []
    service.subscribe(changes.append)
    updated = replace(service.current, appearance=replace(service.current.appearance, font_scale=1.2))

    assert service.update(updated) is True
    assert service.current == updated
    assert changes == [updated]


def test_service_does_not_notify_for_unchanged_settings(tmp_path) -> None:
    service = UserSettingsService(UserSettingsRepository(tmp_path / "settings.json"))
    changes: list[UserSettings] = []
    service.subscribe(changes.append)

    assert service.update(service.current) is False
    assert changes == []


def test_service_reset_notifies_and_persists_defaults(tmp_path) -> None:
    repository = UserSettingsRepository(tmp_path / "settings.json")
    service = UserSettingsService(repository)
    service.update(replace(service.current, system=replace(service.current.system, close_behavior="ask")))

    assert service.reset() is True
    assert repository.load() == UserSettings()
