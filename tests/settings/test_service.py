from dataclasses import replace

import pytest

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


def test_listener_failure_does_not_rollback_saved_settings_or_skip_others(tmp_path) -> None:
    path = tmp_path / "settings.json"
    service = UserSettingsService(UserSettingsRepository(path))
    received = []
    service.subscribe(lambda _settings: (_ for _ in ()).throw(RuntimeError("ui closed")))
    service.subscribe(received.append)
    updated = replace(
        service.current,
        appearance=replace(service.current.appearance, font_scale=1.1),
    )
    assert service.update(updated)
    assert service.current == updated
    assert UserSettingsRepository(path).load() == updated
    assert received == [updated]


def test_unsubscribe_and_type_validation(tmp_path) -> None:
    service = UserSettingsService(UserSettingsRepository(tmp_path / "settings.json"))
    received = []
    listener = received.append
    service.subscribe(listener)
    service.unsubscribe(listener)
    service.update(replace(
        service.current,
        appearance=replace(service.current.appearance, font_scale=1.1),
    ))
    assert received == []
    with pytest.raises(TypeError, match="UserSettings"):
        service.update(object())
