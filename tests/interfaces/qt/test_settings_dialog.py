from PySide6.QtCore import Qt

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
    assert dialog._navigation.item(3).text() == "Ses"
    assert dialog._navigation.item(5).text() == "Hatırlatıcılar"
    assert dialog._navigation.item(6).text() == "Gelişmiş"
    assert dialog._agent_max_steps.minimum() == 3
    assert dialog._agent_max_steps.maximum() == 12
    assert "kalıcı işlem onayı" in dialog._agent_security_note.text()
    assert dialog._agent_security_note.accessibleName()
    assert not dialog._agent_template_suggestions.isChecked()
    assert dialog._agent_interrupted_notice.isChecked()
    assert dialog._agent_history_retention.currentData() == 30
    assert dialog._codex_session_retention.currentData() == 30
    assert dialog._codex_resume.isChecked()
    assert dialog._codex_diff_review.isChecked()
    assert not dialog._codex_diff_review.isEnabled()
    assert dialog._codex_diff_max.value() == 1024
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
    assert dialog._navigation.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    assert "QListWidget#settingsNavigation::item:selected" in dialog.styleSheet()


def test_settings_search_and_density_are_persistent(qtbot, tmp_path) -> None:
    service = UserSettingsService(UserSettingsRepository(tmp_path / "settings.json"))
    dialog = SettingsDialog(service)
    qtbot.addWidget(dialog)
    dialog._settings_search.setText("kalibrasyon")
    visible = [dialog._navigation.item(index).text() for index in range(dialog._navigation.count()) if not dialog._navigation.item(index).isHidden()]
    assert visible == ["Ses"]
    dialog._density.setCurrentIndex(dialog._density.findData("compact"))
    dialog._apply()
    assert service.current.appearance.density == "compact"
