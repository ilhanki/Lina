from lina.interfaces.qt.settings_dialog import SettingsDialog
from lina.settings.repository import UserSettingsRepository
from lina.settings.service import UserSettingsService


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
