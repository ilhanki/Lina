from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from lina.core.exceptions import ConfigurationError
from lina.core.settings import AppSettings, load_settings


def test_load_settings_reads_valid_toml_file(tmp_path: Path) -> None:
    config_path = _write_config(
        tmp_path,
        """
        [app]
        name = "Lina"
        environment = "development"

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
        """,
    )

    settings = load_settings(config_path)

    assert isinstance(settings, AppSettings)
    assert settings.app.name == "Lina"
    assert settings.app.environment == "development"
    assert settings.logging.level == "INFO"
    assert settings.paths.data == "data"
    assert settings.paths.logs == "logs"
    assert settings.paths.models == "models"
    assert settings.paths.cache == "cache"
    assert settings.ollama.base_url == "http://localhost:11434"
    assert settings.ollama.default_model == "llama3"
    assert settings.ollama.request_timeout == 30.0
    assert settings.runtime.conversation_history_limit == 6
    assert settings.runtime.project_context_max_characters == 6000
    assert settings.memory.enabled is True
    assert settings.memory.database_path == "data/lina_memory.sqlite3"
    assert settings.memory.max_context_items == 8
    assert settings.memory.max_context_characters == 1200
    assert settings.speech.enabled is False
    assert settings.speech.stt_provider == "faster_whisper"
    assert settings.speech.model_size == "base"
    assert settings.speech.language == "tr"
    assert settings.speech.device == "cpu"
    assert settings.speech.compute_type == "int8"
    assert settings.speech.sample_rate == 16000
    assert settings.speech.channels == 1
    assert settings.speech.max_recording_seconds == 12.0
    assert settings.speech.auto_send is False
    assert settings.vision.enabled is True
    assert settings.vision.model == "qwen3-vl:2b"
    assert settings.vision.request_timeout == 120.0
    assert settings.vision.max_image_bytes == 8_388_608
    assert settings.vision.consume_attachment_on_success is True


def test_load_settings_reads_local_vision_settings(tmp_path: Path) -> None:
    config_path = _write_config(
        tmp_path,
        """
        [app]
        name = "Lina"
        environment = "development"

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

        [vision]
        enabled = true
        model = "local-vision"
        request_timeout = 90
        max_image_bytes = 1024
        consume_attachment_on_success = false
        """,
    )

    settings = load_settings(config_path).vision

    assert settings.enabled is True
    assert settings.model == "local-vision"
    assert settings.request_timeout == 90.0
    assert settings.max_image_bytes == 1024
    assert settings.consume_attachment_on_success is False


@pytest.mark.parametrize(
    ("vision_config", "error_message"),
    [
        ('enabled = true\nmodel = ""', "vision.model must not be empty"),
        ('request_timeout = 0', "positive number"),
        ('max_image_bytes = 0', "positive integer"),
    ],
)
def test_invalid_vision_settings_raise_configuration_error(
    tmp_path: Path,
    vision_config: str,
    error_message: str,
) -> None:
    config_path = _write_config(
        tmp_path,
        f"""
        [app]
        name = "Lina"
        environment = "development"

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

        [vision]
        {vision_config}
        """,
    )

    with pytest.raises(ConfigurationError, match=error_message):
        load_settings(config_path)


def test_load_settings_reads_optional_runtime_settings(tmp_path: Path) -> None:
    config_path = _write_config(
        tmp_path,
        """
        [app]
        name = "Lina"
        environment = "development"

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
        request_timeout = 12.5

        [runtime]
        conversation_history_limit = 4
        project_context_max_characters = 3000
        """,
    )

    settings = load_settings(config_path)

    assert settings.ollama.request_timeout == 12.5
    assert settings.runtime.conversation_history_limit == 4
    assert settings.runtime.project_context_max_characters == 3000


def test_load_settings_reads_optional_memory_settings(tmp_path: Path) -> None:
    config_path = _write_config(
        tmp_path,
        """
        [app]
        name = "Lina"
        environment = "development"

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
        database_path = "data/test_memory.sqlite3"
        max_context_items = 3
        max_context_characters = 400
        """,
    )

    settings = load_settings(config_path)

    assert settings.memory.enabled is False
    assert settings.memory.database_path == "data/test_memory.sqlite3"
    assert settings.memory.max_context_items == 3
    assert settings.memory.max_context_characters == 400


def test_load_settings_reads_local_speech_settings(tmp_path: Path) -> None:
    config_path = _write_config(
        tmp_path,
        """
        [app]
        name = "Lina"
        environment = "development"

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

        [speech]
        enabled = true
        stt_provider = "faster_whisper"
        model_size = "small"
        language = "tr"
        device = "cpu"
        compute_type = "int8"
        sample_rate = 16000
        channels = 1
        max_recording_seconds = 8
        silence_threshold = 0.02
        silence_duration_seconds = 1.0
        auto_send = false
        """,
    )

    settings = load_settings(config_path).speech

    assert settings.enabled is True
    assert settings.model_size == "small"
    assert settings.max_recording_seconds == 8.0
    assert settings.silence_threshold == 0.02


@pytest.mark.parametrize(
    ("speech_config", "error_message"),
    [
        ('channels = 2', "speech.channels must be 1"),
        ('max_recording_seconds = 31', "must be between 1 and 30"),
        ('sample_rate = 0', "positive integer"),
        ('auto_send = true', "speech.auto_send must be false"),
        ('device = "cuda"', "speech.device must be cpu"),
        ('model_size = "base.en"', "must be multilingual"),
        ('stt_provider = "cloud"', "Unsupported speech.stt_provider"),
    ],
)
def test_invalid_speech_settings_raise_configuration_error(
    tmp_path: Path,
    speech_config: str,
    error_message: str,
) -> None:
    config_path = _write_config(
        tmp_path,
        f"""
        [app]
        name = "Lina"
        environment = "development"

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

        [speech]
        {speech_config}
        """,
    )

    with pytest.raises(ConfigurationError, match=error_message):
        load_settings(config_path)


def test_settings_are_immutable(tmp_path: Path) -> None:
    settings = load_settings(_write_valid_config(tmp_path))

    with pytest.raises(FrozenInstanceError):
        settings.app.name = "Other"


def test_missing_config_file_raises_configuration_error(tmp_path: Path) -> None:
    config_path = tmp_path / "missing.toml"

    with pytest.raises(ConfigurationError, match="Config file not found"):
        load_settings(config_path)


def test_invalid_toml_raises_configuration_error(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path, "[app")

    with pytest.raises(ConfigurationError, match="Invalid TOML config file"):
        load_settings(config_path)


def test_missing_section_raises_configuration_error(tmp_path: Path) -> None:
    config_path = _write_config(
        tmp_path,
        """
        [app]
        name = "Lina"
        environment = "development"
        """,
    )

    with pytest.raises(ConfigurationError, match="Missing config section: logging"):
        load_settings(config_path)


def test_missing_key_raises_configuration_error(tmp_path: Path) -> None:
    config_path = _write_config(
        tmp_path,
        """
        [app]
        name = "Lina"

        [logging]
        level = "INFO"

        [paths]
        data = "data"
        logs = "logs"
        models = "models"
        cache = "cache"

        [ollama]
        base_url = "http://localhost:11434"
        default_model = ""
        """,
    )

    with pytest.raises(ConfigurationError, match="Missing config key: app.environment"):
        load_settings(config_path)


def test_invalid_value_type_raises_configuration_error(tmp_path: Path) -> None:
    config_path = _write_config(
        tmp_path,
        """
        [app]
        name = "Lina"
        environment = "development"

        [logging]
        level = 10

        [paths]
        data = "data"
        logs = "logs"
        models = "models"
        cache = "cache"

        [ollama]
        base_url = "http://localhost:11434"
        default_model = ""
        """,
    )

    with pytest.raises(ConfigurationError, match="Config key must be a string: logging.level"):
        load_settings(config_path)


def test_invalid_section_type_raises_configuration_error(tmp_path: Path) -> None:
    config_path = _write_config(
        tmp_path,
        """
        app = "Lina"

        [logging]
        level = "INFO"

        [paths]
        data = "data"
        logs = "logs"
        models = "models"
        cache = "cache"

        [ollama]
        base_url = "http://localhost:11434"
        default_model = ""
        """,
    )

    with pytest.raises(ConfigurationError, match="Config section must be a table: app"):
        load_settings(config_path)


def test_invalid_optional_runtime_value_raises_configuration_error(tmp_path: Path) -> None:
    config_path = _write_config(
        tmp_path,
        """
        [app]
        name = "Lina"
        environment = "development"

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

        [runtime]
        conversation_history_limit = 0
        """,
    )

    with pytest.raises(ConfigurationError, match="positive integer"):
        load_settings(config_path)


def test_invalid_optional_ollama_timeout_raises_configuration_error(tmp_path: Path) -> None:
    config_path = _write_config(
        tmp_path,
        """
        [app]
        name = "Lina"
        environment = "development"

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
        request_timeout = -1
        """,
    )

    with pytest.raises(ConfigurationError, match="positive number"):
        load_settings(config_path)


def test_invalid_optional_memory_value_raises_configuration_error(tmp_path: Path) -> None:
    config_path = _write_config(
        tmp_path,
        """
        [app]
        name = "Lina"
        environment = "development"

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
        max_context_items = 0
        """,
    )

    with pytest.raises(ConfigurationError, match="positive integer"):
        load_settings(config_path)


def _write_valid_config(tmp_path: Path) -> Path:
    return _write_config(
        tmp_path,
        """
        [app]
        name = "Lina"
        environment = "development"

        [logging]
        level = "INFO"

        [paths]
        data = "data"
        logs = "logs"
        models = "models"
        cache = "cache"

        [ollama]
        base_url = "http://localhost:11434"
        default_model = ""
        """,
    )


def _write_config(tmp_path: Path, content: str) -> Path:
    config_path = tmp_path / "settings.toml"
    config_path.write_text(content, encoding="utf-8")
    return config_path
