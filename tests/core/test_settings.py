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
