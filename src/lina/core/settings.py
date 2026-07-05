"""Application settings loading for Lina."""

from dataclasses import dataclass
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


@dataclass(frozen=True)
class AppSettings:
    """Typed application settings."""

    app: ApplicationSettings
    logging: LoggingSettings
    paths: PathSettings
    ollama: OllamaSettings


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

