"""Framework-neutral models for persistent user preferences."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any


SCHEMA_VERSION = 1
SUPPORTED_THEMES = frozenset({"dark", "light", "system"})
SUPPORTED_CLOSE_BEHAVIORS = frozenset({"exit", "tray", "ask"})


@dataclass(frozen=True, slots=True)
class AppearanceSettings:
    theme: str = "dark"
    font_scale: float = 1.0
    compact_mode: bool = False
    reduce_motion: bool = False


@dataclass(frozen=True, slots=True)
class GeneralSettings:
    language: str = "tr"
    open_last_conversation: bool = True
    confirm_before_delete: bool = True
    welcome_enabled: bool = True
    intent_routing_enabled: bool = True


@dataclass(frozen=True, slots=True)
class ModelSettings:
    text_model: str = "llama3.2:3b"
    vision_model: str = "qwen3-vl:2b"


@dataclass(frozen=True, slots=True)
class SpeechUserSettings:
    enabled: bool = True
    language: str = "tr"
    auto_insert_transcription: bool = True


@dataclass(frozen=True, slots=True)
class VisionUserSettings:
    enabled: bool = True
    consume_attachment_on_success: bool = True


@dataclass(frozen=True, slots=True)
class SystemSettings:
    minimize_to_tray: bool = False
    close_behavior: str = "exit"
    start_minimized: bool = False
    notifications_enabled: bool = True
    reminders_enabled: bool = True
    desktop_notifications_enabled: bool = True
    show_missed_reminders: bool = True


@dataclass(frozen=True, slots=True)
class UserSettings:
    """Validated, serializable user preferences."""

    schema_version: int = SCHEMA_VERSION
    appearance: AppearanceSettings = AppearanceSettings()
    general: GeneralSettings = GeneralSettings()
    models: ModelSettings = ModelSettings()
    speech: SpeechUserSettings = SpeechUserSettings()
    vision: VisionUserSettings = VisionUserSettings()
    system: SystemSettings = SystemSettings()

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("Unsupported user settings schema version")
        if self.appearance.theme not in SUPPORTED_THEMES:
            raise ValueError("Unsupported appearance theme")
        if not 0.85 <= self.appearance.font_scale <= 1.35:
            raise ValueError("Appearance font scale must be between 0.85 and 1.35")
        if self.general.language != "tr":
            raise ValueError("Only Turkish user settings are supported")
        if self.speech.language != "tr":
            raise ValueError("Only Turkish speech settings are supported")
        if self.system.close_behavior not in SUPPORTED_CLOSE_BEHAVIORS:
            raise ValueError("Unsupported close behavior")
        _validate_model_name(self.models.text_model)
        _validate_model_name(self.models.vision_model)

    def to_dict(self) -> dict[str, Any]:
        """Return only the safe user preference schema."""
        return {
            "schema_version": self.schema_version,
            "appearance": {
                "theme": self.appearance.theme,
                "font_scale": self.appearance.font_scale,
                "compact_mode": self.appearance.compact_mode,
                "reduce_motion": self.appearance.reduce_motion,
            },
            "general": {
                "language": self.general.language,
                "open_last_conversation": self.general.open_last_conversation,
                "confirm_before_delete": self.general.confirm_before_delete,
                "welcome_enabled": self.general.welcome_enabled,
                "intent_routing_enabled": self.general.intent_routing_enabled,
            },
            "models": {
                "text_model": self.models.text_model,
                "vision_model": self.models.vision_model,
            },
            "speech": {
                "enabled": self.speech.enabled,
                "language": self.speech.language,
                "auto_insert_transcription": self.speech.auto_insert_transcription,
            },
            "vision": {
                "enabled": self.vision.enabled,
                "consume_attachment_on_success": self.vision.consume_attachment_on_success,
            },
            "system": {
                "minimize_to_tray": self.system.minimize_to_tray,
                "close_behavior": self.system.close_behavior,
                "start_minimized": self.system.start_minimized,
                "notifications_enabled": self.system.notifications_enabled,
                "reminders_enabled": self.system.reminders_enabled,
                "desktop_notifications_enabled": self.system.desktop_notifications_enabled,
                "show_missed_reminders": self.system.show_missed_reminders,
            },
        }

    @classmethod
    def from_dict(cls, raw: object) -> "UserSettings":
        """Parse known fields and use safe defaults for missing or invalid values."""
        if not isinstance(raw, dict):
            return cls()
        if raw.get("schema_version") not in (None, SCHEMA_VERSION):
            return cls()
        defaults = cls()
        appearance = _section(raw, "appearance")
        general = _section(raw, "general")
        models = _section(raw, "models")
        speech = _section(raw, "speech")
        vision = _section(raw, "vision")
        system = _section(raw, "system")
        return cls(
            appearance=AppearanceSettings(
                theme=_choice(appearance, "theme", defaults.appearance.theme, SUPPORTED_THEMES),
                font_scale=_bounded_float(appearance, "font_scale", defaults.appearance.font_scale, 0.85, 1.35),
                compact_mode=_bool(appearance, "compact_mode", defaults.appearance.compact_mode),
                reduce_motion=_bool(appearance, "reduce_motion", defaults.appearance.reduce_motion),
            ),
            general=GeneralSettings(
                language=_choice(general, "language", "tr", {"tr"}),
                open_last_conversation=_bool(general, "open_last_conversation", defaults.general.open_last_conversation),
                confirm_before_delete=_bool(general, "confirm_before_delete", defaults.general.confirm_before_delete),
                welcome_enabled=_bool(general, "welcome_enabled", defaults.general.welcome_enabled),
                intent_routing_enabled=_bool(general, "intent_routing_enabled", defaults.general.intent_routing_enabled),
            ),
            models=ModelSettings(
                text_model=_model_name(models, "text_model", defaults.models.text_model),
                vision_model=_model_name(models, "vision_model", defaults.models.vision_model),
            ),
            speech=SpeechUserSettings(
                enabled=_bool(speech, "enabled", defaults.speech.enabled),
                language=_choice(speech, "language", "tr", {"tr"}),
                auto_insert_transcription=_bool(speech, "auto_insert_transcription", defaults.speech.auto_insert_transcription),
            ),
            vision=VisionUserSettings(
                enabled=_bool(vision, "enabled", defaults.vision.enabled),
                consume_attachment_on_success=_bool(vision, "consume_attachment_on_success", defaults.vision.consume_attachment_on_success),
            ),
            system=SystemSettings(
                minimize_to_tray=_bool(system, "minimize_to_tray", defaults.system.minimize_to_tray),
                close_behavior=_choice(system, "close_behavior", defaults.system.close_behavior, SUPPORTED_CLOSE_BEHAVIORS),
                start_minimized=_bool(system, "start_minimized", defaults.system.start_minimized),
                notifications_enabled=_bool(system, "notifications_enabled", defaults.system.notifications_enabled),
                reminders_enabled=_bool(system, "reminders_enabled", defaults.system.reminders_enabled),
                desktop_notifications_enabled=_bool(system, "desktop_notifications_enabled", defaults.system.desktop_notifications_enabled),
                show_missed_reminders=_bool(system, "show_missed_reminders", defaults.system.show_missed_reminders),
            ),
        )


def _section(raw: dict[str, Any], name: str) -> dict[str, Any]:
    value = raw.get(name)
    return value if isinstance(value, dict) else {}


def _bool(section: dict[str, Any], key: str, default: bool) -> bool:
    value = section.get(key)
    return value if isinstance(value, bool) else default


def _choice(section: dict[str, Any], key: str, default: str, choices: set[str] | frozenset[str]) -> str:
    value = section.get(key)
    return value if isinstance(value, str) and value in choices else default


def _bounded_float(section: dict[str, Any], key: str, default: float, minimum: float, maximum: float) -> float:
    value = section.get(key)
    if isinstance(value, (int, float)) and not isinstance(value, bool) and minimum <= value <= maximum:
        return float(value)
    return default


def _model_name(section: dict[str, Any], key: str, default: str) -> str:
    value = section.get(key)
    if not isinstance(value, str):
        return default
    candidate = value.strip()
    try:
        _validate_model_name(candidate)
    except ValueError:
        return default
    return candidate


def _validate_model_name(value: str) -> None:
    if not value or len(value) > 120 or any(character.isspace() and character != " " for character in value):
        raise ValueError("Model name is invalid")
    if any(character in value for character in "\r\n\x00"):
        raise ValueError("Model name contains control characters")
