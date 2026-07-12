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
class SpeechSettings:
    """Local speech capability settings."""

    enabled: bool = False
    stt_provider: str = "faster_whisper"
    model_size: str = "base"
    language: str = "tr"
    device: str = "cpu"
    compute_type: str = "int8"
    sample_rate: int = 16000
    channels: int = 1
    max_recording_seconds: float = 12.0
    silence_threshold: float = 0.015
    silence_duration_seconds: float = 1.2
    auto_send: bool = False


@dataclass(frozen=True)
class VisionSettings:
    """Local vision capability settings."""

    enabled: bool = True
    model: str = "qwen3-vl:2b"
    request_timeout: float = 120.0
    max_image_bytes: int = 8_388_608
    consume_attachment_on_success: bool = True


@dataclass(frozen=True)
class ConversationSettings:
    """Local persistent conversation history settings."""

    enabled: bool = True
    database_path: str = "data/conversations.sqlite3"
    max_sidebar_sessions: int = 50
    max_loaded_messages: int = 500
    model_history_messages: int = 30
    open_last_conversation_on_startup: bool = True


@dataclass(frozen=True)
class AppSettings:
    """Typed application settings."""

    app: ApplicationSettings
    logging: LoggingSettings
    paths: PathSettings
    ollama: OllamaSettings
    runtime: RuntimeSettings = field(default_factory=RuntimeSettings)
    memory: MemorySettings = field(default_factory=MemorySettings)
    speech: SpeechSettings = field(default_factory=SpeechSettings)
    vision: VisionSettings = field(default_factory=VisionSettings)
    conversations: ConversationSettings = field(default_factory=ConversationSettings)


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
        speech=_load_speech_settings(raw_settings),
        vision=_load_vision_settings(raw_settings),
        conversations=_load_conversation_settings(raw_settings),
    )


def _load_conversation_settings(settings: dict[str, Any]) -> ConversationSettings:
    return ConversationSettings(
        enabled=_optional_bool(settings, "conversations", "enabled", True),
        database_path=_optional_string(
            settings,
            "conversations",
            "database_path",
            "data/conversations.sqlite3",
        ),
        max_sidebar_sessions=_optional_positive_int(
            settings, "conversations", "max_sidebar_sessions", 50
        ),
        max_loaded_messages=_optional_positive_int(
            settings, "conversations", "max_loaded_messages", 500
        ),
        model_history_messages=_optional_positive_int(
            settings, "conversations", "model_history_messages", 30
        ),
        open_last_conversation_on_startup=_optional_bool(
            settings, "conversations", "open_last_conversation_on_startup", True
        ),
    )


def _load_vision_settings(settings: dict[str, Any]) -> VisionSettings:
    section = _optional_section(settings, "vision")
    enabled = _optional_bool(settings, "vision", "enabled", True)
    raw_model = section.get("model", "qwen3-vl:2b")
    if not isinstance(raw_model, str):
        raise ConfigurationError("Config key must be a string: vision.model")
    model = raw_model.strip()
    if enabled and not model:
        raise ConfigurationError("vision.model must not be empty when vision is enabled")
    return VisionSettings(
        enabled=enabled,
        model=model,
        request_timeout=_optional_positive_float(
            settings,
            "vision",
            "request_timeout",
            120.0,
        ),
        max_image_bytes=_optional_positive_int(
            settings,
            "vision",
            "max_image_bytes",
            8_388_608,
        ),
        consume_attachment_on_success=_optional_bool(
            settings,
            "vision",
            "consume_attachment_on_success",
            True,
        ),
    )


def _load_speech_settings(settings: dict[str, Any]) -> SpeechSettings:
    speech = SpeechSettings(
        enabled=_optional_bool(settings, "speech", "enabled", False),
        stt_provider=_optional_string(
            settings,
            "speech",
            "stt_provider",
            "faster_whisper",
        ),
        model_size=_optional_string(settings, "speech", "model_size", "base"),
        language=_optional_string(settings, "speech", "language", "tr"),
        device=_optional_string(settings, "speech", "device", "cpu"),
        compute_type=_optional_string(settings, "speech", "compute_type", "int8"),
        sample_rate=_optional_positive_int(settings, "speech", "sample_rate", 16000),
        channels=_optional_positive_int(settings, "speech", "channels", 1),
        max_recording_seconds=_optional_positive_float(
            settings,
            "speech",
            "max_recording_seconds",
            12.0,
        ),
        silence_threshold=_optional_positive_float(
            settings,
            "speech",
            "silence_threshold",
            0.015,
        ),
        silence_duration_seconds=_optional_positive_float(
            settings,
            "speech",
            "silence_duration_seconds",
            1.2,
        ),
        auto_send=_optional_bool(settings, "speech", "auto_send", False),
    )
    _validate_speech_settings(speech)
    return speech


def _validate_speech_settings(settings: SpeechSettings) -> None:
    if settings.stt_provider not in {"faster_whisper", "noop"}:
        raise ConfigurationError("Unsupported speech.stt_provider")
    if settings.model_size.casefold().endswith(".en"):
        raise ConfigurationError("speech.model_size must be multilingual")
    if settings.language.casefold() != "tr":
        raise ConfigurationError("speech.language must be tr")
    if settings.device.casefold() != "cpu":
        raise ConfigurationError("speech.device must be cpu")
    if settings.channels != 1:
        raise ConfigurationError("speech.channels must be 1")
    if not 1.0 <= settings.max_recording_seconds <= 30.0:
        raise ConfigurationError(
            "speech.max_recording_seconds must be between 1 and 30"
        )
    if not 0.0 < settings.silence_threshold <= 1.0:
        raise ConfigurationError("speech.silence_threshold must be between 0 and 1")
    if settings.silence_duration_seconds > settings.max_recording_seconds:
        raise ConfigurationError(
            "speech.silence_duration_seconds cannot exceed max recording duration"
        )
    if settings.auto_send:
        raise ConfigurationError("speech.auto_send must be false")


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
