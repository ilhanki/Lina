from lina.interfaces.qt.settings_dialog import SettingsDialog
from lina.settings.models import UserSettings
from lina.settings.repository import UserSettingsRepository
from lina.settings.service import UserSettingsService
from lina.interfaces.qt.theme import build_stylesheet


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


def test_settings_dialog_supports_theme_and_font_scale_options(qtbot, tmp_path) -> None:
    service = UserSettingsService(UserSettingsRepository(tmp_path / "settings.json"))
    dialog = SettingsDialog(service)
    qtbot.addWidget(dialog)

    assert {dialog._theme.itemData(index) for index in range(dialog._theme.count())} == {
        "dark", "light", "system"
    }
    dialog._theme.setCurrentIndex(dialog._theme.findData("light"))
    dialog._font_scale.setValue(135)
    dialog._apply()

    assert service.current.appearance.theme == "light"
    assert service.current.appearance.font_scale == 1.35
    dialog.setStyleSheet(build_stylesheet("Segoe UI", "light", 1.35))
    assert dialog._navigation.objectName() == "settingsNavigation"
    assert dialog._pages.objectName() == "settingsPages"
    assert "QListWidget#settingsNavigation::item:selected" in dialog.styleSheet()
