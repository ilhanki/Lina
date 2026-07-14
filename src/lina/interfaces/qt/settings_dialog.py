"""PySide6 user settings dialog."""

from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import QThreadPool, Qt, Signal
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
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from lina.settings.models import UserSettings
from lina.settings.service import UserSettingsService
from lina.interfaces.qt.worker import FunctionWorker
from lina.speech.audio_devices import AudioInputDeviceService


class SettingsDialog(QDialog):
    """Edit a local working copy of Lina user preferences."""

    settings_applied = Signal(object)

    def __init__(
        self,
        settings_service: UserSettingsService,
        model_diagnostics=None,
        vision_diagnostics=None,
        voice_controller=None,
        inference_diagnostics=None,
        privacy_confirmation=None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._settings_service = settings_service
        self._model_diagnostics = model_diagnostics
        self._vision_diagnostics = vision_diagnostics
        self._voice_controller = voice_controller
        self._inference_diagnostics = inference_diagnostics
        self._privacy_confirmation = privacy_confirmation or self._show_hands_free_privacy_confirmation
        self._benchmark_worker = None
        self._benchmark_cancelled = False
        self._refresh_worker = None
        self._refresh_generation = 0
        self._audio_worker = None
        self._audio_devices = AudioInputDeviceService()
        self._vision_valid_models: set[str] = set()
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
        self._navigation.setObjectName("settingsNavigation")
        self._navigation.setFixedWidth(150)
        self._navigation.addItems(
            ["Genel", "Görünüm", "Modeller", "Konuşma", "Vision", "Sistem", "Hakkında"]
        )
        content.addWidget(self._navigation)
        self._pages = QStackedWidget(self)
        self._pages.setObjectName("settingsPages")
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
        self._intent_routing = QCheckBox("Akıllı araç yönlendirme", page)
        form.addRow("Dil", self._language)
        form.addRow(self._open_last)
        form.addRow(self._confirm_delete)
        form.addRow(self._welcome)
        form.addRow(self._intent_routing)
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
        self._keep_alive = QComboBox(page)
        self._keep_alive.addItem("Kapalı", "0")
        self._keep_alive.addItem("5 dakika", "5m")
        self._keep_alive.addItem("15 dakika", "15m")
        self._keep_alive.addItem("Sürekli", "-1")
        self._max_output_tokens = QSpinBox(page)
        self._max_output_tokens.setRange(32, 8192)
        self._context_budget = QSpinBox(page)
        self._context_budget.setRange(1000, 100000)
        self._context_budget.setSingleStep(1000)
        self._warm_up = QCheckBox("Modeli açılışta arka planda hazırla", page)
        self._refresh_models = QPushButton("Modelleri Yenile", page)
        self._model_status = QLabel("", page)
        form.addRow("Text model", self._text_model)
        form.addRow("Vision model", self._vision_model)
        form.addRow("Modeli bellekte tut", self._keep_alive)
        form.addRow("Maksimum cevap uzunluğu", self._max_output_tokens)
        form.addRow("Context bütçesi", self._context_budget)
        form.addRow(self._warm_up)
        form.addRow(self._refresh_models)
        form.addRow(self._model_status)
        self._performance_status = QLabel("Henüz ölçüm yok.", page)
        self._performance_status.setWordWrap(True)
        self._benchmark_button = QPushButton("Performans Testi", page)
        self._benchmark_button.setEnabled(self._inference_diagnostics is not None)
        self._benchmark_button.clicked.connect(self._toggle_benchmark)
        form.addRow(self._benchmark_button)
        form.addRow(self._performance_status)
        self._refresh_models.clicked.connect(self._refresh_model_list)
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
        self._voice_responses = QCheckBox("Sesli yanıtlar etkin", page)
        self._system_voice = QComboBox(page)
        self._system_voice.addItem("Varsayılan sistem sesi", None)
        if self._voice_controller is not None:
            for voice in self._voice_controller.list_voices():
                self._system_voice.addItem(voice.name, voice.id)
        self._speech_rate = QSlider(Qt.Orientation.Horizontal, page)
        self._speech_rate.setRange(50, 200)
        self._volume = QSlider(Qt.Orientation.Horizontal, page)
        self._volume.setRange(0, 100)
        self._transcription_mode = QComboBox(page)
        self._transcription_mode.addItem("Composer'a ekle", "insert")
        self._transcription_mode.addItem("Otomatik gönder", "send")
        self._barge_in = QCheckBox("Lina konuşurken mikrofonla sesi kes", page)
        self._hands_free = QCheckBox("Hands-free conversation", page)
        self._wake_word = QCheckBox("Wake word (Deneysel)", page)
        self._wake_phrase = QLineEdit(page)
        self._wake_indicator = QCheckBox("Wake-word listening indicator", page)
        self._return_to_wake = QCheckBox("Lina cevap verdikten sonra tekrar dinlemeye dön", page)
        self._voice_confirmation = QCheckBox("Confirmation cevaplarını sesle kabul et", page)
        self._microphone_device = QComboBox(page)
        self._microphone_device.addItem("Varsayılan mikrofon", None)
        self._refresh_microphones = QPushButton("Mikrofonları Yenile", page)
        self._test_microphone = QPushButton("Mikrofonu Test Et", page)
        self._microphone_status = QLabel("", page)
        wake_available = bool(self._voice_controller and self._voice_controller.wake_word_available)
        self._hands_free.setEnabled(wake_available)
        self._wake_word.setEnabled(wake_available)
        if not wake_available:
            self._wake_word.setToolTip("Bu sürümde detector kurulu değil.")
            self._hands_free.setToolTip("Wake-word algılama şu anda kullanılamıyor.")
        form.addRow(self._speech_enabled)
        form.addRow("Dil", self._speech_language)
        form.addRow(self._voice_responses)
        form.addRow("Sistem sesi", self._system_voice)
        form.addRow("Konuşma hızı", self._speech_rate)
        form.addRow("Ses seviyesi", self._volume)
        form.addRow("Transcription davranışı", self._transcription_mode)
        form.addRow(self._barge_in)
        form.addRow(self._hands_free)
        form.addRow(self._wake_word)
        form.addRow("Wake phrase", self._wake_phrase)
        form.addRow(self._wake_indicator)
        form.addRow(self._return_to_wake)
        form.addRow(self._voice_confirmation)
        form.addRow("Mikrofon", self._microphone_device)
        microphone_actions = QWidget(page)
        microphone_layout = QHBoxLayout(microphone_actions)
        microphone_layout.setContentsMargins(0, 0, 0, 0)
        microphone_layout.addWidget(self._refresh_microphones)
        microphone_layout.addWidget(self._test_microphone)
        form.addRow(microphone_actions)
        form.addRow(self._microphone_status)
        self._hands_free.clicked.connect(self._confirm_hands_free_enable)
        self._refresh_microphones.clicked.connect(self._refresh_audio_input_devices)
        self._test_microphone.clicked.connect(self._test_selected_microphone)
        self._refresh_audio_input_devices()
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
        self._reminders_enabled = QCheckBox("Hatırlatıcıları etkinleştir", page)
        self._desktop_notifications = QCheckBox("Masaüstü bildirimleri", page)
        self._show_missed = QCheckBox("Kaçırılanları açılışta göster", page)
        form.addRow(self._minimize_to_tray)
        form.addRow("Kapanış davranışı", self._close_behavior)
        form.addRow(self._start_minimized)
        form.addRow(self._notifications)
        form.addRow(self._reminders_enabled)
        form.addRow(self._desktop_notifications)
        form.addRow(self._show_missed)
        return page

    def _about_page(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        label = QLabel(
            "Lina\n\nLocal-first kişisel yapay zeka asistanı.\n"
            "Ayarlar yalnızca bu cihazda tutulur; sohbet ve hafıza verileri bu dosyaya yazılmaz.\n\n"
            "Lina araç işlemlerinde yalnız tür, durum ve süre gibi teknik bilgileri loglar.",
            page,
        )
        label.setWordWrap(True)
        layout.addWidget(label)
        privacy = QLabel(
            "Ses işleme yereldir. Wake word varsayılan olarak kapalıdır; audio kayıtları "
            "saklanmaz. Lina konuşurken sesi manuel olarak durdurabilirsin.",
            page,
        )
        privacy.setWordWrap(True)
        layout.addWidget(privacy)
        layout.addStretch(1)
        return page

    def _load_settings(self, settings: UserSettings) -> None:
        self._draft = settings
        _select_data(self._language, settings.general.language)
        self._open_last.setChecked(settings.general.open_last_conversation)
        self._confirm_delete.setChecked(settings.general.confirm_before_delete)
        self._welcome.setChecked(settings.general.welcome_enabled)
        self._intent_routing.setChecked(settings.general.intent_routing_enabled)
        _select_data(self._theme, settings.appearance.theme)
        self._font_scale.setValue(round(settings.appearance.font_scale * 100))
        self._compact_mode.setChecked(settings.appearance.compact_mode)
        self._reduce_motion.setChecked(settings.appearance.reduce_motion)
        self._text_model.setText(settings.models.text_model)
        self._vision_model.setText(settings.models.vision_model)
        _select_data(self._keep_alive, settings.models.keep_alive)
        self._max_output_tokens.setValue(settings.models.max_output_tokens)
        self._context_budget.setValue(settings.models.context_budget)
        self._warm_up.setChecked(settings.models.warm_up_enabled)
        self._speech_enabled.setChecked(settings.speech.enabled)
        _select_data(self._speech_language, settings.speech.language)
        self._voice_responses.setChecked(settings.speech.voice_responses_enabled)
        _select_data(self._system_voice, settings.speech.system_voice)
        self._speech_rate.setValue(round(settings.speech.speech_rate * 100))
        self._volume.setValue(round(settings.speech.volume * 100))
        _select_data(self._transcription_mode, settings.speech.transcription_mode)
        self._barge_in.setChecked(settings.speech.barge_in_enabled)
        self._hands_free.setChecked(settings.speech.hands_free_enabled)
        self._wake_word.setChecked(settings.speech.wake_word_enabled and self._wake_word.isEnabled())
        self._wake_phrase.setText(settings.speech.wake_phrase)
        self._wake_indicator.setChecked(settings.speech.wake_word_indicator_enabled)
        self._return_to_wake.setChecked(settings.speech.return_to_wake_listening)
        self._voice_confirmation.setChecked(settings.speech.voice_confirmation_enabled)
        _select_data(self._microphone_device, settings.speech.microphone_device_id)
        self._vision_enabled.setChecked(settings.vision.enabled)
        self._vision_consume.setChecked(settings.vision.consume_attachment_on_success)
        self._minimize_to_tray.setChecked(settings.system.minimize_to_tray)
        _select_data(self._close_behavior, settings.system.close_behavior)
        self._start_minimized.setChecked(settings.system.start_minimized)
        self._notifications.setChecked(settings.system.notifications_enabled)
        self._reminders_enabled.setChecked(settings.system.reminders_enabled)
        self._desktop_notifications.setChecked(settings.system.desktop_notifications_enabled)
        self._show_missed.setChecked(settings.system.show_missed_reminders)

    def _collect_settings(self) -> UserSettings:
        return UserSettings(
            appearance=replace(
                self._draft.appearance,
                theme=str(self._theme.currentData()),
                font_scale=self._font_scale.value() / 100,
                compact_mode=self._compact_mode.isChecked(),
                reduce_motion=self._reduce_motion.isChecked(),
            ),
            general=replace(
                self._draft.general,
                language=str(self._language.currentData()),
                open_last_conversation=self._open_last.isChecked(),
                confirm_before_delete=self._confirm_delete.isChecked(),
                welcome_enabled=self._welcome.isChecked(),
                intent_routing_enabled=self._intent_routing.isChecked(),
            ),
            models=replace(
                self._draft.models,
                text_model=self._text_model.text().strip(),
                vision_model=self._validated_vision_model(),
                keep_alive=str(self._keep_alive.currentData()),
                max_output_tokens=self._max_output_tokens.value(),
                context_budget=self._context_budget.value(),
                warm_up_enabled=self._warm_up.isChecked(),
            ),
            speech=replace(
                self._draft.speech,
                enabled=self._speech_enabled.isChecked(),
                language=str(self._speech_language.currentData()),
                auto_insert_transcription=self._transcription_mode.currentData() == "insert",
                voice_responses_enabled=self._voice_responses.isChecked(),
                system_voice=self._system_voice.currentData(),
                speech_rate=self._speech_rate.value() / 100,
                volume=self._volume.value() / 100,
                transcription_mode=str(self._transcription_mode.currentData()),
                barge_in_enabled=self._barge_in.isChecked(),
                hands_free_enabled=self._hands_free.isChecked(),
                wake_word_enabled=(self._wake_word.isChecked() or self._hands_free.isChecked())
                and self._wake_word.isEnabled(),
                wake_phrase=self._wake_phrase.text().strip() or "Hey Lina",
                wake_word_indicator_enabled=self._wake_indicator.isChecked(),
                return_to_wake_listening=self._return_to_wake.isChecked(),
                voice_confirmation_enabled=self._voice_confirmation.isChecked(),
                microphone_device_id=self._microphone_device.currentData(),
            ),
            vision=replace(
                self._draft.vision,
                enabled=self._vision_enabled.isChecked(),
                consume_attachment_on_success=self._vision_consume.isChecked(),
            ),
            system=replace(
                self._draft.system,
                minimize_to_tray=self._minimize_to_tray.isChecked(),
                close_behavior=str(self._close_behavior.currentData()),
                start_minimized=self._start_minimized.isChecked(),
                notifications_enabled=self._notifications.isChecked(),
                reminders_enabled=self._reminders_enabled.isChecked(),
                desktop_notifications_enabled=self._desktop_notifications.isChecked(),
                show_missed_reminders=self._show_missed.isChecked(),
            ),
        )

    def _validated_vision_model(self) -> str:
        model = self._vision_model.text().strip()
        if (
            self._vision_diagnostics is not None
            and model != self._draft.models.vision_model
            and model not in self._vision_valid_models
        ):
            raise ValueError("Seçilen model görsel analiz desteğine sahip değil.")
        return model

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

    def _confirm_hands_free_enable(self, checked: bool) -> None:
        if not checked or self._draft.speech.hands_free_enabled:
            return
        if self._privacy_confirmation():
            self._wake_word.setChecked(True)
        else:
            self._hands_free.setChecked(False)

    def _show_hands_free_privacy_confirmation(self) -> bool:
        box = QMessageBox(self)
        box.setWindowTitle("Hands-free conversation")
        box.setText(
            "Hands-free modunda Lina, “Hey Lina” ifadesini algılamak için mikrofonu "
            "yerel olarak dinler. Ses kayıtları saklanmaz ve cloud’a gönderilmez."
        )
        enable = box.addButton("Etkinleştir", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("Vazgeç", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        return box.clickedButton() is enable

    def _refresh_audio_input_devices(self) -> None:
        if self._audio_worker is not None:
            return
        self._refresh_microphones.setEnabled(False)
        worker = FunctionWorker(self._audio_devices.list_devices)
        self._audio_worker = worker
        worker.signals.result.connect(self._show_audio_input_devices)
        worker.signals.error.connect(lambda _error: self._microphone_status.setText("Mikrofona erişilemiyor."))
        worker.signals.finished.connect(lambda: self._finish_audio_worker(worker))
        QThreadPool.globalInstance().start(worker)

    def _show_audio_input_devices(self, devices: object) -> None:
        selected = self._microphone_device.currentData()
        self._microphone_device.clear()
        self._microphone_device.addItem("Varsayılan mikrofon", None)
        for device in devices if isinstance(devices, tuple) else ():
            self._microphone_device.addItem(device.name, device.id)
        _select_data(self._microphone_device, selected)
        available_ids = {device.id for device in devices} if isinstance(devices, tuple) else set()
        if selected is not None and selected not in available_ids:
            self._microphone_status.setText("Seçili mikrofon kullanılamıyor. Varsayılan mikrofon kullanılıyor.")
        else:
            self._microphone_status.setText(f"{len(devices)} giriş aygıtı bulundu." if devices else "Kullanılabilir mikrofon bulunamadı.")

    def _test_selected_microphone(self) -> None:
        if self._audio_worker is not None:
            return
        self._test_microphone.setEnabled(False)
        worker = FunctionWorker(self._audio_devices.test_device, self._microphone_device.currentData())
        self._audio_worker = worker
        worker.signals.result.connect(lambda ready: self._microphone_status.setText("Mikrofon hazır." if ready else "Mikrofona erişilemiyor."))
        worker.signals.error.connect(lambda _error: self._microphone_status.setText("Mikrofona erişilemiyor."))
        worker.signals.finished.connect(lambda: self._finish_audio_worker(worker))
        QThreadPool.globalInstance().start(worker)

    def _finish_audio_worker(self, worker: object) -> None:
        if self._audio_worker is worker:
            self._audio_worker = None
            self._refresh_microphones.setEnabled(True)
            self._test_microphone.setEnabled(True)

    def _refresh_model_list(self) -> None:
        if self._model_diagnostics is None or self._refresh_worker is not None:
            return
        self._refresh_generation += 1
        generation = self._refresh_generation
        self._refresh_models.setEnabled(False)
        self._model_status.setText("Modeller kontrol ediliyor...")
        worker = FunctionWorker(self._load_models_and_validate_vision)
        self._refresh_worker = worker
        worker.signals.result.connect(lambda result: self._handle_model_list(generation, result))
        worker.signals.error.connect(lambda error: self._handle_model_refresh_error(generation, error))
        worker.signals.finished.connect(lambda: self._finish_model_refresh(worker))
        QThreadPool.globalInstance().start(worker)

    def _toggle_benchmark(self) -> None:
        if self._benchmark_worker is not None:
            self._benchmark_cancelled = True
            self._performance_status.setText("Performans testi iptal ediliyor...")
            self._inference_diagnostics.cancel()
            return
        self._run_benchmark()

    def _run_benchmark(self) -> None:
        if self._inference_diagnostics is None or self._benchmark_worker is not None:
            return
        self._benchmark_cancelled = False
        self._benchmark_button.setText("Testi Durdur")
        self._performance_status.setText("Performans ölçülüyor...")
        worker = FunctionWorker(self._inference_diagnostics.benchmark)
        self._benchmark_worker = worker
        worker.signals.result.connect(self._show_benchmark)
        worker.signals.error.connect(self._show_benchmark_error)
        worker.signals.finished.connect(lambda: self._finish_benchmark(worker))
        QThreadPool.globalInstance().start(worker)

    def _show_benchmark_error(self, _error: object) -> None:
        self._performance_status.setText(
            "Performans testi iptal edildi."
            if self._benchmark_cancelled
            else "Ollama'ya ulaşılamadı."
        )

    def _show_benchmark(self, metrics: object) -> None:
        first = getattr(metrics, "first_token_ms", None)
        speed = getattr(metrics, "tokens_per_second", None)
        total = getattr(metrics, "total_ms", None)
        prompt = getattr(metrics, "prompt_tokens", None)
        generated = getattr(metrics, "generated_tokens", None)
        load = getattr(metrics, "load_ms", None)
        lines = [f"Son model: {getattr(metrics, 'model', '-')}"]
        lines.append(f"İlk token: {first / 1000:.1f} sn" if first is not None else "İlk token: -")
        lines.append(f"Hız: {speed:.1f} token/sn" if speed is not None else "Hız: -")
        lines.append(f"Toplam: {total / 1000:.1f} sn" if total is not None else "Toplam: -")
        lines.append(f"Prompt / generated: {prompt or '-'} / {generated or '-'}")
        lines.append(f"Model yükleme: {load / 1000:.1f} sn" if load is not None else "Model yükleme: -")
        self._performance_status.setText("\n".join(lines))

    def _finish_benchmark(self, worker: object) -> None:
        if self._benchmark_worker is worker:
            self._benchmark_worker = None
            self._benchmark_button.setText("Performans Testi")
            self._benchmark_button.setEnabled(True)

    def _load_models_and_validate_vision(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        models = self._model_diagnostics.list_models()
        valid_vision: list[str] = []
        if self._vision_diagnostics is not None:
            for model in models:
                result = self._vision_diagnostics.validate_model(model)
                if result.status.value == "ready":
                    valid_vision.append(model)
        return models, tuple(valid_vision)

    def _handle_model_list(self, generation: int, result: object) -> None:
        if generation != self._refresh_generation or not self.isVisible():
            return
        models = result[0] if isinstance(result, tuple) and len(result) == 2 else ()
        self._vision_valid_models = set(result[1]) if isinstance(result, tuple) and len(result) == 2 else set()
        self._model_status.setText(
            f"{len(models)} yerel model bulundu."
            if models
            else "Kurulu model bulunamadı; mevcut seçimler korundu."
        )

    def _handle_model_refresh_error(self, generation: int, _error: object) -> None:
        if generation == self._refresh_generation and self.isVisible():
            self._model_status.setText("Ollama'ya ulaşılamadı. Mevcut model ayarları korunuyor.")

    def _finish_model_refresh(self, worker: object) -> None:
        if self._refresh_worker is worker:
            self._refresh_worker = None
            self._refresh_models.setEnabled(True)


def _select_data(combo: QComboBox, value: str) -> None:
    index = combo.findData(value)
    if index >= 0:
        combo.setCurrentIndex(index)
