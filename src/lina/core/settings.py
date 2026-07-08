"""Application settings loading for Lina."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import tomllib

from lina.core.exceptions import ConfigurationError


@dataclass(frozen=True)
class ApplicationSettings:
    """Application identity and environment settings."""

    name: str
    environment: str


@dataclass(frozen=True)
class LoggingSettings:
    """Logging settings."""

    level: str


@dataclass(frozen=True)
class PathSettings:
    """Configured runtime path names."""

    data: str
    logs: str
    models: str
    cache: str


@dataclass(frozen=True)
class OllamaSettings:
    """Ollama provider settings."""

    base_url: str
    default_model: str
    request_timeout: float = 30.0


@dataclass(frozen=True)
class RuntimeSettings:
    """Runtime behavior settings."""

    conversation_history_limit: int = 6
    project_context_max_characters: int = 6000


@dataclass(frozen=True)
class MemorySettings:
    """Memory capability settings."""

    enabled: bool = True
    database_path: str = "data/lina_memory.sqlite3"
    max_context_items: int = 8
    max_context_characters: int = 1200


@dataclass(frozen=True)
class AppSettings:
    """Typed application settings."""

    app: ApplicationSettings
    logging: LoggingSettings
    paths: PathSettings
    ollama: OllamaSettings
    runtime: RuntimeSettings = field(default_factory=RuntimeSettings)
    memory: MemorySettings = field(default_factory=MemorySettings)


def load_settings(config_path: Path) -> AppSettings:
    """Load application settings from a TOML file."""
    try:
        with config_path.open("rb") as config_file:
            raw_settings = tomllib.load(config_file)
    except FileNotFoundError as error:
        raise ConfigurationError(f"Config file not found: {config_path}") from error
    except tomllib.TOMLDecodeError as error:
        raise ConfigurationError(f"Invalid TOML config file: {config_path}") from error
    except OSError as error:
        raise ConfigurationError(f"Unable to read config file: {config_path}") from error

    return AppSettings(
        app=ApplicationSettings(
            name=_require_string(raw_settings, "app", "name"),
            environment=_require_string(raw_settings, "app", "environment"),
        ),
        logging=LoggingSettings(
            level=_require_string(raw_settings, "logging", "level"),
        ),
        paths=PathSettings(
            data=_require_string(raw_settings, "paths", "data"),
            logs=_require_string(raw_settings, "paths", "logs"),
            models=_require_string(raw_settings, "paths", "models"),
            cache=_require_string(raw_settings, "paths", "cache"),
        ),
        ollama=OllamaSettings(
            base_url=_require_string(raw_settings, "ollama", "base_url"),
            default_model=_require_string(raw_settings, "ollama", "default_model"),
            request_timeout=_optional_positive_float(
                raw_settings,
                "ollama",
                "request_timeout",
                30.0,
            ),
        ),
        runtime=RuntimeSettings(
            conversation_history_limit=_optional_positive_int(
                raw_settings,
                "runtime",
                "conversation_history_limit",
                6,
            ),
            project_context_max_characters=_optional_positive_int(
                raw_settings,
                "runtime",
                "project_context_max_characters",
                6000,
            ),
        ),
        memory=MemorySettings(
            enabled=_optional_bool(raw_settings, "memory", "enabled", True),
            database_path=_optional_string(
                raw_settings,
                "memory",
                "database_path",
                "data/lina_memory.sqlite3",
            ),
            max_context_items=_optional_positive_int(
                raw_settings,
                "memory",
                "max_context_items",
                8,
            ),
            max_context_characters=_optional_positive_int(
                raw_settings,
                "memory",
                "max_context_characters",
                1200,
            ),
        ),
    )


def _require_string(settings: dict[str, Any], section_name: str, key: str) -> str:
    section = _require_section(settings, section_name)

    if key not in section:
        raise ConfigurationError(f"Missing config key: {section_name}.{key}")

    value = section[key]
    if not isinstance(value, str):
        raise ConfigurationError(f"Config key must be a string: {section_name}.{key}")

    return value


def _require_section(settings: dict[str, Any], section_name: str) -> dict[str, Any]:
    if section_name not in settings:
        raise ConfigurationError(f"Missing config section: {section_name}")

    section = settings[section_name]
    if not isinstance(section, dict):
        raise ConfigurationError(f"Config section must be a table: {section_name}")

    return section


def _optional_section(settings: dict[str, Any], section_name: str) -> dict[str, Any]:
    if section_name not in settings:
        return {}

    section = settings[section_name]
    if not isinstance(section, dict):
        raise ConfigurationError(f"Config section must be a table: {section_name}")

    return section


def _optional_positive_int(
    settings: dict[str, Any],
    section_name: str,
    key: str,
    default: int,
) -> int:
    section = _optional_section(settings, section_name)
    if key not in section:
        return default

    value = section[key]
    if not isinstance(value, int):
        raise ConfigurationError(f"Config key must be an integer: {section_name}.{key}")
    if value <= 0:
        raise ConfigurationError(
            f"Config key must be a positive integer: {section_name}.{key}"
        )

    return value


def _optional_string(
    settings: dict[str, Any],
    section_name: str,
    key: str,
    default: str,
) -> str:
    section = _optional_section(settings, section_name)
    if key not in section:
        return default

    value = section[key]
    if not isinstance(value, str):
        raise ConfigurationError(f"Config key must be a string: {section_name}.{key}")
    if not value.strip():
        raise ConfigurationError(f"Config key must not be empty: {section_name}.{key}")

    return value


def _optional_bool(
    settings: dict[str, Any],
    section_name: str,
    key: str,
    default: bool,
) -> bool:
    section = _optional_section(settings, section_name)
    if key not in section:
        return default

    value = section[key]
    if not isinstance(value, bool):
        raise ConfigurationError(f"Config key must be a boolean: {section_name}.{key}")

    return value


def _optional_positive_float(
    settings: dict[str, Any],
    section_name: str,
    key: str,
    default: float,
) -> float:
    section = _optional_section(settings, section_name)
    if key not in section:
        return default

    value = section[key]
    if not isinstance(value, int | float):
        raise ConfigurationError(f"Config key must be a number: {section_name}.{key}")
    if value <= 0:
        raise ConfigurationError(
            f"Config key must be a positive number: {section_name}.{key}"
        )

    return float(value)
