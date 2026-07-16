from lina.interfaces.qt.settings_dialog import SettingsDialog
from lina.settings.repository import UserSettingsRepository
from lina.settings.service import UserSettingsService


class AvailableVoiceController:
    wake_word_available = True

    def list_voices(self):
        return ()


def test_voice_and_performance_controls_are_present(qtbot, tmp_path):
    service = UserSettingsService(UserSettingsRepository(tmp_path / "settings.json"))
    dialog = SettingsDialog(service)
    qtbot.addWidget(dialog)
    assert dialog._voice_responses.text() == "Sesli yanıtlar etkin"
    assert dialog._transcription_mode.count() == 2
    assert dialog._wake_word.text().endswith("(Deneysel)")
    assert not dialog._wake_word.isEnabled()
    assert dialog._benchmark_button.text() == "Performans Testi"
    assert not dialog._benchmark_button.isEnabled()
    assert not dialog._hands_free.isEnabled()
    assert dialog._calibrate_microphone.text() == "Mikrofonu Kalibre Et"
    assert dialog._wake_test.text() == "Hey Lina’yı Test Et"


def test_dialog_collects_send_mode_and_bounds(qtbot, tmp_path):
    service = UserSettingsService(UserSettingsRepository(tmp_path / "settings.json"))
    dialog = SettingsDialog(service)
    qtbot.addWidget(dialog)
    dialog._voice_responses.setChecked(True)
    dialog._transcription_mode.setCurrentIndex(1)
    dialog._speech_rate.setValue(150)
    dialog._volume.setValue(30)
    collected = dialog._collect_settings()
    assert collected.speech.voice_responses_enabled
    assert collected.speech.transcription_mode == "send"
    assert not collected.speech.auto_insert_transcription
    assert collected.speech.speech_rate == 1.5
    assert collected.speech.volume == 0.3
    assert collected.speech.input_sensitivity == "balanced"


def test_benchmark_button_cancels_active_test(qtbot, tmp_path):
    class Diagnostics:
        cancelled = False

        def benchmark(self):
            return None

        def cancel(self):
            self.cancelled = True

    diagnostics = Diagnostics()
    service = UserSettingsService(UserSettingsRepository(tmp_path / "settings.json"))
    dialog = SettingsDialog(service, inference_diagnostics=diagnostics)
    qtbot.addWidget(dialog)
    dialog._benchmark_worker = object()
    dialog._toggle_benchmark()
    assert diagnostics.cancelled
    assert dialog._benchmark_cancelled
    assert "iptal" in dialog._performance_status.text().casefold()


def test_hands_free_privacy_acceptance_enables_wake_and_collects_defaults(qtbot, tmp_path):
    service = UserSettingsService(UserSettingsRepository(tmp_path / "settings.json"))
    dialog = SettingsDialog(
        service,
        voice_controller=AvailableVoiceController(),
        privacy_confirmation=lambda: True,
    )
    qtbot.addWidget(dialog)
    dialog._hands_free.click()
    collected = dialog._collect_settings()
    assert collected.speech.hands_free_enabled
    assert collected.speech.wake_word_enabled
    assert collected.speech.return_to_wake_listening
    assert collected.speech.voice_confirmation_enabled
    assert collected.speech.wake_word_indicator_enabled


def test_hands_free_privacy_rejection_keeps_microphone_off(qtbot, tmp_path):
    service = UserSettingsService(UserSettingsRepository(tmp_path / "settings.json"))
    dialog = SettingsDialog(
        service,
        voice_controller=AvailableVoiceController(),
        privacy_confirmation=lambda: False,
    )
    qtbot.addWidget(dialog)
    dialog._hands_free.click()
    assert not dialog._hands_free.isChecked()
    assert not dialog._collect_settings().speech.hands_free_enabled
