"""PySide6 user settings dialog."""

from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from lina.settings.models import UserSettings
from lina.settings.service import UserSettingsService


class SettingsDialog(QDialog):
    """Edit a local working copy of Lina user preferences."""

    settings_applied = Signal(object)

    def __init__(self, settings_service: UserSettingsService, parent=None) -> None:
        super().__init__(parent)
        self._settings_service = settings_service
        self._draft = settings_service.current
        self._build_ui()
        self._load_settings(self._draft)

    def _build_ui(self) -> None:
        self.setWindowTitle("Ayarlar")
        self.setMinimumSize(720, 520)
        self.resize(820, 620)
        root = QVBoxLayout(self)
        content = QHBoxLayout()
        self._navigation = QListWidget(self)
        self._navigation.setFixedWidth(150)
        self._navigation.addItems(
            ["Genel", "Görünüm", "Modeller", "Konuşma", "Vision", "Sistem", "Hakkında"]
        )
        content.addWidget(self._navigation)
        self._pages = QStackedWidget(self)
        self._pages.addWidget(self._general_page())
        self._pages.addWidget(self._appearance_page())
        self._pages.addWidget(self._models_page())
        self._pages.addWidget(self._speech_page())
        self._pages.addWidget(self._vision_page())
        self._pages.addWidget(self._system_page())
        self._pages.addWidget(self._about_page())
        self._navigation.currentRowChanged.connect(self._pages.setCurrentIndex)
        content.addWidget(self._pages, 1)
        root.addLayout(content, 1)

        actions = QHBoxLayout()
        self._reset_button = QPushButton("Varsayılanlara Dön", self)
        self._cancel_button = QPushButton("Vazgeç", self)
        self._apply_button = QPushButton("Uygula", self)
        self._save_button = QPushButton("Kaydet", self)
        self._save_button.setObjectName("accentButton")
        actions.addWidget(self._reset_button)
        actions.addStretch(1)
        actions.addWidget(self._cancel_button)
        actions.addWidget(self._apply_button)
        actions.addWidget(self._save_button)
        root.addLayout(actions)
        self._navigation.setCurrentRow(0)
        self._reset_button.clicked.connect(self._reset_form)
        self._cancel_button.clicked.connect(self.reject)
        self._apply_button.clicked.connect(self._apply)
        self._save_button.clicked.connect(self._save)

    def _general_page(self) -> QWidget:
        page = QWidget(self)
        form = QFormLayout(page)
        self._language = QComboBox(page)
        self._language.addItem("Türkçe", "tr")
        self._open_last = QCheckBox("Son sohbeti başlangıçta aç", page)
        self._confirm_delete = QCheckBox("Sohbet silmeden önce onayla", page)
        self._welcome = QCheckBox("Welcome alanını göster", page)
        form.addRow("Dil", self._language)
        form.addRow(self._open_last)
        form.addRow(self._confirm_delete)
        form.addRow(self._welcome)
        return page

    def _appearance_page(self) -> QWidget:
        page = QWidget(self)
        form = QFormLayout(page)
        self._theme = QComboBox(page)
        self._theme.addItem("Koyu", "dark")
        self._theme.addItem("Açık", "light")
        self._theme.addItem("Sistem", "system")
        self._font_scale = QSlider(Qt.Orientation.Horizontal, page)
        self._font_scale.setRange(85, 135)
        self._font_scale.setSingleStep(5)
        self._compact_mode = QCheckBox("Kompakt sohbet listesi", page)
        self._reduce_motion = QCheckBox("Animasyonları azalt", page)
        form.addRow("Tema", self._theme)
        form.addRow("Yazı ölçeği", self._font_scale)
        form.addRow(self._compact_mode)
        form.addRow(self._reduce_motion)
        return page

    def _models_page(self) -> QWidget:
        page = QWidget(self)
        form = QFormLayout(page)
        self._text_model = QLineEdit(page)
        self._vision_model = QLineEdit(page)
        form.addRow("Text model", self._text_model)
        form.addRow("Vision model", self._vision_model)
        note = QLabel("Yalnız cihazında kurulu Ollama modellerini kullan.", page)
        note.setWordWrap(True)
        form.addRow(note)
        return page

    def _speech_page(self) -> QWidget:
        page = QWidget(self)
        form = QFormLayout(page)
        self._speech_enabled = QCheckBox("Konuşma özelliğini etkinleştir", page)
        self._speech_language = QComboBox(page)
        self._speech_language.addItem("Türkçe", "tr")
        self._speech_insert = QCheckBox("Transkripsiyonu composer'a ekle", page)
        form.addRow(self._speech_enabled)
        form.addRow("Dil", self._speech_language)
        form.addRow(self._speech_insert)
        return page

    def _vision_page(self) -> QWidget:
        page = QWidget(self)
        form = QFormLayout(page)
        self._vision_enabled = QCheckBox("Vision özelliğini etkinleştir", page)
        self._vision_consume = QCheckBox("Başarılı analizden sonra attachment'ı kaldır", page)
        form.addRow(self._vision_enabled)
        form.addRow(self._vision_consume)
        return page

    def _system_page(self) -> QWidget:
        page = QWidget(self)
        form = QFormLayout(page)
        self._minimize_to_tray = QCheckBox("Kapatınca sistem tepsisine küçült", page)
        self._close_behavior = QComboBox(page)
        self._close_behavior.addItem("Uygulamadan çık", "exit")
        self._close_behavior.addItem("Sistem tepsisine küçült", "tray")
        self._close_behavior.addItem("Her seferinde sor", "ask")
        self._start_minimized = QCheckBox("Başlangıçta küçültülmüş başlat", page)
        self._notifications = QCheckBox("Masaüstü bildirimlerini etkinleştir", page)
        form.addRow(self._minimize_to_tray)
        form.addRow("Kapanış davranışı", self._close_behavior)
        form.addRow(self._start_minimized)
        form.addRow(self._notifications)
        return page

    def _about_page(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        label = QLabel(
            "Lina\n\nLocal-first kişisel yapay zeka asistanı.\n"
            "Ayarlar yalnızca bu cihazda tutulur; sohbet ve hafıza verileri bu dosyaya yazılmaz.",
            page,
        )
        label.setWordWrap(True)
        layout.addWidget(label)
        layout.addStretch(1)
        return page

    def _load_settings(self, settings: UserSettings) -> None:
        self._draft = settings
        _select_data(self._language, settings.general.language)
        self._open_last.setChecked(settings.general.open_last_conversation)
        self._confirm_delete.setChecked(settings.general.confirm_before_delete)
        self._welcome.setChecked(settings.general.welcome_enabled)
        _select_data(self._theme, settings.appearance.theme)
        self._font_scale.setValue(round(settings.appearance.font_scale * 100))
        self._compact_mode.setChecked(settings.appearance.compact_mode)
        self._reduce_motion.setChecked(settings.appearance.reduce_motion)
        self._text_model.setText(settings.models.text_model)
        self._vision_model.setText(settings.models.vision_model)
        self._speech_enabled.setChecked(settings.speech.enabled)
        _select_data(self._speech_language, settings.speech.language)
        self._speech_insert.setChecked(settings.speech.auto_insert_transcription)
        self._vision_enabled.setChecked(settings.vision.enabled)
        self._vision_consume.setChecked(settings.vision.consume_attachment_on_success)
        self._minimize_to_tray.setChecked(settings.system.minimize_to_tray)
        _select_data(self._close_behavior, settings.system.close_behavior)
        self._start_minimized.setChecked(settings.system.start_minimized)
        self._notifications.setChecked(settings.system.notifications_enabled)

    def _collect_settings(self) -> UserSettings:
        return UserSettings(
            appearance=replace(self._draft.appearance, theme=str(self._theme.currentData()), font_scale=self._font_scale.value() / 100, compact_mode=self._compact_mode.isChecked(), reduce_motion=self._reduce_motion.isChecked()),
            general=replace(self._draft.general, language=str(self._language.currentData()), open_last_conversation=self._open_last.isChecked(), confirm_before_delete=self._confirm_delete.isChecked(), welcome_enabled=self._welcome.isChecked()),
            models=replace(self._draft.models, text_model=self._text_model.text().strip(), vision_model=self._vision_model.text().strip()),
            speech=replace(self._draft.speech, enabled=self._speech_enabled.isChecked(), language=str(self._speech_language.currentData()), auto_insert_transcription=self._speech_insert.isChecked()),
            vision=replace(self._draft.vision, enabled=self._vision_enabled.isChecked(), consume_attachment_on_success=self._vision_consume.isChecked()),
            system=replace(self._draft.system, minimize_to_tray=self._minimize_to_tray.isChecked(), close_behavior=str(self._close_behavior.currentData()), start_minimized=self._start_minimized.isChecked(), notifications_enabled=self._notifications.isChecked()),
        )

    def _apply(self) -> None:
        try:
            settings = self._collect_settings()
            self._settings_service.update(settings)
            self._draft = settings
            self.settings_applied.emit(settings)
        except (ValueError, OSError) as error:
            QMessageBox.warning(self, "Ayarlar", f"Ayarlar kaydedilemedi: {error}")

    def _save(self) -> None:
        self._apply()
        if self._draft == self._settings_service.current:
            self.accept()

    def _reset_form(self) -> None:
        self._load_settings(UserSettings())


def _select_data(combo: QComboBox, value: str) -> None:
    index = combo.findData(value)
    if index >= 0:
        combo.setCurrentIndex(index)
