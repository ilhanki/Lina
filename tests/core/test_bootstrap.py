import pytest
from pathlib import Path
from lina.core.bootstrap import create_application_services
from lina.speech.models import SpeechState
from lina.speech.audio_recorder import SoundDeviceAudioRecorder
from lina.speech.faster_whisper_provider import FasterWhisperSTTProvider

def test_bootstrap_wires_services_correctly(tmp_path: Path) -> None:
    config_path = tmp_path / "settings.toml"
    config_path.write_text("""
[app]
name = "Lina"
environment = "test"

[logging]
level = "INFO"

[paths]
data = "data"
logs = "logs"
models = "models"
cache = "cache"

[ollama]
base_url = "http://localhost:11434"
default_model = "llama3"
request_timeout = 15.0

[runtime]
conversation_history_limit = 5
project_context_max_characters = 1000

[memory]
enabled = true
database_path = "data/test_memory.sqlite3"
max_context_items = 4
max_context_characters = 500
    """, encoding="utf-8")

    services = create_application_services(config_path, tmp_path)

    try:
        assert services.application is not None
        assert services.conversation_service is not None
        assert services.diagnostics_service is not None
        assert services.speech_service is not None
        assert services.speech_service.is_stt_available() is False
        assert services.speech_service.is_tts_available() is False
        assert services.speech_service.get_state() is SpeechState.IDLE
        assert services.conversation_service._history_limit == 5
        assert services.diagnostics_service._timeout == 5.0  # Min check in bootstrap
        assert services.vision_diagnostics_service.configured_model == "qwen3-vl:2b"
        assert services.vision_diagnostics_service._timeout == 5.0
        vision_provider = services.conversation_service._vision_brain._model_provider
        assert vision_provider._model == "qwen3-vl:2b"
        assert vision_provider._timeout == 120.0
        assert vision_provider._max_image_bytes == 8_388_608
        assert services.conversation_service._memory_service is not None
        assert (tmp_path / "data" / "test_memory.sqlite3").exists()
        assert services.conversation_service._context_manager._memory_context_max_items == 4
        assert services.conversation_service._context_manager._memory_context_max_characters == 500
    finally:
        services.conversation_service._memory_service.close()


def test_bootstrap_can_disable_memory(tmp_path: Path) -> None:
    config_path = tmp_path / "settings.toml"
    config_path.write_text("""
[app]
name = "Lina"
environment = "test"

[logging]
level = "INFO"

[paths]
data = "data"
logs = "logs"
models = "models"
cache = "cache"

[ollama]
base_url = "http://localhost:11434"
default_model = "llama3"

[memory]
enabled = false
    """, encoding="utf-8")

    services = create_application_services(config_path, tmp_path)

    assert services.conversation_service._memory_service is None


def test_bootstrap_wires_local_speech_without_loading_model(tmp_path: Path) -> None:
    config_path = tmp_path / "settings.toml"
    config_path.write_text("""
[app]
name = "Lina"
environment = "test"

[logging]
level = "INFO"

[paths]
data = "data"
logs = "logs"
models = "models"
cache = "cache"

[ollama]
base_url = "http://localhost:11434"
default_model = "llama3"

[memory]
enabled = false

[speech]
enabled = true
stt_provider = "faster_whisper"
model_size = "base"
language = "tr"
device = "cpu"
compute_type = "int8"
sample_rate = 16000
channels = 1
max_recording_seconds = 8
silence_threshold = 0.015
silence_duration_seconds = 1.2
auto_send = false
    """, encoding="utf-8")

    services = create_application_services(config_path, tmp_path)

    assert isinstance(
        services.speech_service._audio_recorder,
        SoundDeviceAudioRecorder,
    )
    assert isinstance(
        services.speech_service._stt_provider,
        FasterWhisperSTTProvider,
    )
    assert services.speech_service._stt_provider._model is None
