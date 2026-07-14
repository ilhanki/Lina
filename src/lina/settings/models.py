"""Framework-neutral models for persistent user preferences."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any


SCHEMA_VERSION = 5
SUPPORTED_THEMES = frozenset({"dark", "light", "system"})
SUPPORTED_CLOSE_BEHAVIORS = frozenset({"exit", "tray", "ask"})
SUPPORTED_TRANSCRIPTION_MODES = frozenset({"insert", "send"})
SUPPORTED_KEEP_ALIVE = frozenset({"0", "5m", "15m", "-1"})
SUPPORTED_LIVE_VISION_SOURCES = frozenset({"camera", "screen", "region"})
SUPPORTED_CHANGE_SENSITIVITY = frozenset({"low", "medium", "high"})


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
    keep_alive: str = "5m"
    max_output_tokens: int = 512
    context_budget: int = 12000
    warm_up_enabled: bool = False


@dataclass(frozen=True, slots=True)
class SpeechUserSettings:
    enabled: bool = True
    language: str = "tr"
    auto_insert_transcription: bool = True
    voice_responses_enabled: bool = False
    system_voice: str | None = None
    speech_rate: float = 1.0
    volume: float = 1.0
    transcription_mode: str = "insert"
    barge_in_enabled: bool = True
    hands_free_enabled: bool = False
    wake_word_enabled: bool = False
    wake_phrase: str = "Hey Lina"
    wake_word_indicator_enabled: bool = True
    return_to_wake_listening: bool = True
    voice_confirmation_enabled: bool = True
    microphone_device_id: int | None = None


@dataclass(frozen=True, slots=True)
class VisionUserSettings:
    enabled: bool = True
    consume_attachment_on_success: bool = True


@dataclass(frozen=True, slots=True)
class LiveVisionUserSettings:
    enabled: bool = True
    default_source: str = "screen"
    capture_interval_seconds: float = 2.0
    minimum_analysis_interval_seconds: float = 5.0
    monitor_duration_minutes: int = 5
    change_sensitivity: str = "medium"
    voice_live_vision_enabled: bool = True
    speak_only_meaningful_changes: bool = True
    camera_device_id: str | None = None
    default_screen_name: str | None = None
    realtime_camera_conversation_enabled: bool = True
    automatic_camera_commentary_enabled: bool = True
    mirror_camera_preview: bool = True
    speak_semantic_changes: bool = True
    commentary_cooldown_seconds: float = 10.0
    camera_analysis_interval_seconds: float = 3.0


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
    live_vision: LiveVisionUserSettings = LiveVisionUserSettings()
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
        if self.speech.transcription_mode not in SUPPORTED_TRANSCRIPTION_MODES:
            raise ValueError("Unsupported transcription mode")
        _validate_wake_phrase(self.speech.wake_phrase)
        if not 0.5 <= self.speech.speech_rate <= 2.0:
            raise ValueError("Speech rate must be between 0.5 and 2.0")
        if not 0.0 <= self.speech.volume <= 1.0:
            raise ValueError("Speech volume must be between 0.0 and 1.0")
        if self.models.keep_alive not in SUPPORTED_KEEP_ALIVE:
            raise ValueError("Unsupported model keep-alive")
        if not 32 <= self.models.max_output_tokens <= 8192:
            raise ValueError("Maximum output tokens must be between 32 and 8192")
        if not 1000 <= self.models.context_budget <= 100000:
            raise ValueError("Context budget must be between 1000 and 100000")
        if self.system.close_behavior not in SUPPORTED_CLOSE_BEHAVIORS:
            raise ValueError("Unsupported close behavior")
        if self.live_vision.default_source not in SUPPORTED_LIVE_VISION_SOURCES:
            raise ValueError("Unsupported live vision source")
        if self.live_vision.change_sensitivity not in SUPPORTED_CHANGE_SENSITIVITY:
            raise ValueError("Unsupported live vision sensitivity")
        if not 0.5 <= self.live_vision.capture_interval_seconds <= 60:
            raise ValueError("Live vision capture interval must be between 0.5 and 60")
        if not 1 <= self.live_vision.minimum_analysis_interval_seconds <= 3600:
            raise ValueError("Live vision analysis interval must be between 1 and 3600")
        if self.live_vision.monitor_duration_minutes not in {0, 1, 5, 15}:
            raise ValueError("Unsupported live vision duration")
        if not 8 <= self.live_vision.commentary_cooldown_seconds <= 60:
            raise ValueError("Camera commentary cooldown must be between 8 and 60")
        if not 2 <= self.live_vision.camera_analysis_interval_seconds <= 60:
            raise ValueError("Camera analysis interval must be between 2 and 60")
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
                "keep_alive": self.models.keep_alive,
                "max_output_tokens": self.models.max_output_tokens,
                "context_budget": self.models.context_budget,
                "warm_up_enabled": self.models.warm_up_enabled,
            },
            "speech": {
                "enabled": self.speech.enabled,
                "language": self.speech.language,
                "auto_insert_transcription": self.speech.auto_insert_transcription,
                "voice_responses_enabled": self.speech.voice_responses_enabled,
                "system_voice": self.speech.system_voice,
                "speech_rate": self.speech.speech_rate,
                "volume": self.speech.volume,
                "transcription_mode": self.speech.transcription_mode,
                "barge_in_enabled": self.speech.barge_in_enabled,
                "hands_free_enabled": self.speech.hands_free_enabled,
                "wake_word_enabled": self.speech.wake_word_enabled,
                "wake_phrase": self.speech.wake_phrase,
                "wake_word_indicator_enabled": self.speech.wake_word_indicator_enabled,
                "return_to_wake_listening": self.speech.return_to_wake_listening,
                "voice_confirmation_enabled": self.speech.voice_confirmation_enabled,
                "microphone_device_id": self.speech.microphone_device_id,
            },
            "vision": {
                "enabled": self.vision.enabled,
                "consume_attachment_on_success": self.vision.consume_attachment_on_success,
            },
            "live_vision": {
                "enabled": self.live_vision.enabled,
                "default_source": self.live_vision.default_source,
                "capture_interval_seconds": self.live_vision.capture_interval_seconds,
                "minimum_analysis_interval_seconds": self.live_vision.minimum_analysis_interval_seconds,
                "monitor_duration_minutes": self.live_vision.monitor_duration_minutes,
                "change_sensitivity": self.live_vision.change_sensitivity,
                "voice_live_vision_enabled": self.live_vision.voice_live_vision_enabled,
                "speak_only_meaningful_changes": self.live_vision.speak_only_meaningful_changes,
                "camera_device_id": self.live_vision.camera_device_id,
                "default_screen_name": self.live_vision.default_screen_name,
                "realtime_camera_conversation_enabled": self.live_vision.realtime_camera_conversation_enabled,
                "automatic_camera_commentary_enabled": self.live_vision.automatic_camera_commentary_enabled,
                "mirror_camera_preview": self.live_vision.mirror_camera_preview,
                "speak_semantic_changes": self.live_vision.speak_semantic_changes,
                "commentary_cooldown_seconds": self.live_vision.commentary_cooldown_seconds,
                "camera_analysis_interval_seconds": self.live_vision.camera_analysis_interval_seconds,
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
        if raw.get("schema_version") not in (None, 1, 2, 3, 4, SCHEMA_VERSION):
            return cls()
        defaults = cls()
        appearance = _section(raw, "appearance")
        general = _section(raw, "general")
        models = _section(raw, "models")
        speech = _section(raw, "speech")
        vision = _section(raw, "vision")
        live_vision = _section(raw, "live_vision")
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
                keep_alive=_choice(models, "keep_alive", defaults.models.keep_alive, SUPPORTED_KEEP_ALIVE),
                max_output_tokens=_bounded_int(models, "max_output_tokens", defaults.models.max_output_tokens, 32, 8192),
                context_budget=_bounded_int(models, "context_budget", defaults.models.context_budget, 1000, 100000),
                warm_up_enabled=_bool(models, "warm_up_enabled", defaults.models.warm_up_enabled),
            ),
            speech=SpeechUserSettings(
                enabled=_bool(speech, "enabled", defaults.speech.enabled),
                language=_choice(speech, "language", "tr", {"tr"}),
                auto_insert_transcription=_bool(speech, "auto_insert_transcription", defaults.speech.auto_insert_transcription),
                voice_responses_enabled=_bool(speech, "voice_responses_enabled", defaults.speech.voice_responses_enabled),
                system_voice=_optional_string(speech, "system_voice"),
                speech_rate=_bounded_float(speech, "speech_rate", defaults.speech.speech_rate, 0.5, 2.0),
                volume=_bounded_float(speech, "volume", defaults.speech.volume, 0.0, 1.0),
                transcription_mode=_choice(
                    speech,
                    "transcription_mode",
                    "send"
                    if speech.get("auto_insert_transcription") is False
                    else defaults.speech.transcription_mode,
                    SUPPORTED_TRANSCRIPTION_MODES,
                ),
                barge_in_enabled=_bool(speech, "barge_in_enabled", defaults.speech.barge_in_enabled),
                hands_free_enabled=_bool(speech, "hands_free_enabled", defaults.speech.hands_free_enabled),
                wake_word_enabled=_bool(speech, "wake_word_enabled", defaults.speech.wake_word_enabled),
                wake_phrase=_wake_phrase(speech, defaults.speech.wake_phrase),
                wake_word_indicator_enabled=_bool(speech, "wake_word_indicator_enabled", defaults.speech.wake_word_indicator_enabled),
                return_to_wake_listening=_bool(speech, "return_to_wake_listening", defaults.speech.return_to_wake_listening),
                voice_confirmation_enabled=_bool(speech, "voice_confirmation_enabled", defaults.speech.voice_confirmation_enabled),
                microphone_device_id=_optional_int(speech, "microphone_device_id"),
            ),
            vision=VisionUserSettings(
                enabled=_bool(vision, "enabled", defaults.vision.enabled),
                consume_attachment_on_success=_bool(vision, "consume_attachment_on_success", defaults.vision.consume_attachment_on_success),
            ),
            live_vision=LiveVisionUserSettings(
                enabled=_bool(live_vision, "enabled", defaults.live_vision.enabled),
                default_source=_choice(live_vision, "default_source", defaults.live_vision.default_source, SUPPORTED_LIVE_VISION_SOURCES),
                capture_interval_seconds=_bounded_float(live_vision, "capture_interval_seconds", defaults.live_vision.capture_interval_seconds, 0.5, 60),
                minimum_analysis_interval_seconds=_bounded_float(live_vision, "minimum_analysis_interval_seconds", defaults.live_vision.minimum_analysis_interval_seconds, 1, 3600),
                monitor_duration_minutes=_choice_int(live_vision, "monitor_duration_minutes", defaults.live_vision.monitor_duration_minutes, {0, 1, 5, 15}),
                change_sensitivity=_choice(live_vision, "change_sensitivity", defaults.live_vision.change_sensitivity, SUPPORTED_CHANGE_SENSITIVITY),
                voice_live_vision_enabled=_bool(live_vision, "voice_live_vision_enabled", defaults.live_vision.voice_live_vision_enabled),
                speak_only_meaningful_changes=_bool(live_vision, "speak_only_meaningful_changes", defaults.live_vision.speak_only_meaningful_changes),
                camera_device_id=_optional_string(live_vision, "camera_device_id"),
                default_screen_name=_optional_string(live_vision, "default_screen_name"),
                realtime_camera_conversation_enabled=_bool(live_vision, "realtime_camera_conversation_enabled", defaults.live_vision.realtime_camera_conversation_enabled),
                automatic_camera_commentary_enabled=_bool(live_vision, "automatic_camera_commentary_enabled", defaults.live_vision.automatic_camera_commentary_enabled),
                mirror_camera_preview=_bool(live_vision, "mirror_camera_preview", defaults.live_vision.mirror_camera_preview),
                speak_semantic_changes=_bool(live_vision, "speak_semantic_changes", defaults.live_vision.speak_semantic_changes),
                commentary_cooldown_seconds=_bounded_float(live_vision, "commentary_cooldown_seconds", defaults.live_vision.commentary_cooldown_seconds, 8, 60),
                camera_analysis_interval_seconds=_bounded_float(live_vision, "camera_analysis_interval_seconds", defaults.live_vision.camera_analysis_interval_seconds, 2, 60),
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


def _choice_int(section: dict[str, Any], key: str, default: int, choices: set[int]) -> int:
    value = section.get(key)
    return value if isinstance(value, int) and not isinstance(value, bool) and value in choices else default


def _bounded_float(section: dict[str, Any], key: str, default: float, minimum: float, maximum: float) -> float:
    value = section.get(key)
    if isinstance(value, (int, float)) and not isinstance(value, bool) and minimum <= value <= maximum:
        return float(value)
    return default


def _bounded_int(section: dict[str, Any], key: str, default: int, minimum: int, maximum: int) -> int:
    value = section.get(key)
    return value if isinstance(value, int) and not isinstance(value, bool) and minimum <= value <= maximum else default


def _optional_string(section: dict[str, Any], key: str) -> str | None:
    value = section.get(key)
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    return candidate[:500] if candidate else None


def _optional_int(section: dict[str, Any], key: str) -> int | None:
    value = section.get(key)
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _safe_string(section: dict[str, Any], key: str, default: str, maximum: int) -> str:
    value = section.get(key)
    if not isinstance(value, str):
        return default
    candidate = value.strip()
    return candidate[:maximum] if candidate else default


def _wake_phrase(section: dict[str, Any], default: str) -> str:
    candidate = _safe_string(section, "wake_phrase", default, 40)
    try:
        _validate_wake_phrase(candidate)
    except ValueError:
        return default
    return candidate


def _validate_wake_phrase(value: str) -> None:
    normalized = " ".join(re.sub(r"[^\w\s]", " ", value.casefold()).split())
    if not 2 <= len(normalized) <= 40 or len(normalized.split()) not in {2, 3}:
        raise ValueError("Wake phrase must contain two or three short words")


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
