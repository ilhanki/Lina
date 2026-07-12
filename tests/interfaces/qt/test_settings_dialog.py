from lina.interfaces.qt.settings_dialog import SettingsDialog
from lina.settings.models import UserSettings
from lina.settings.repository import UserSettingsRepository
from lina.settings.service import UserSettingsService


def test_settings_dialog_loads_sections_and_saves_values(qtbot, tmp_path) -> None:
    service = UserSettingsService(UserSettingsRepository(tmp_path / "settings.json"))
    dialog = SettingsDialog(service)
    qtbot.addWidget(dialog)

    assert dialog._navigation.count() == 7
    dialog._font_scale.setValue(120)
    dialog._apply()

    assert service.current.appearance.font_scale == 1.2
    assert service.current == service._repository.load()


def test_settings_dialog_reset_only_changes_working_copy(qtbot, tmp_path) -> None:
    service = UserSettingsService(UserSettingsRepository(tmp_path / "settings.json"))
    dialog = SettingsDialog(service)
    qtbot.addWidget(dialog)
    dialog._font_scale.setValue(130)

    dialog._reset_form()

    assert dialog._font_scale.value() == 100
    assert service.current == UserSettings()


def test_settings_dialog_save_closes(qtbot, tmp_path) -> None:
    service = UserSettingsService(UserSettingsRepository(tmp_path / "settings.json"))
    dialog = SettingsDialog(service)
    qtbot.addWidget(dialog)
    dialog.show()

    dialog._save()

    assert not dialog.isVisible()
