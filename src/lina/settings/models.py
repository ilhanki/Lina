"""Framework-neutral models for persistent user preferences."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


SCHEMA_VERSION = 11
SUPPORTED_THEMES = frozenset({"dark", "light", "system"})
SUPPORTED_CLOSE_BEHAVIORS = frozenset({"exit", "tray", "ask"})
SUPPORTED_TRANSCRIPTION_MODES = frozenset({"insert", "send"})
SUPPORTED_KEEP_ALIVE = frozenset({"0", "5m", "15m", "-1"})
SUPPORTED_LIVE_VISION_SOURCES = frozenset({"camera", "screen", "region"})
SUPPORTED_CHANGE_SENSITIVITY = frozenset({"low", "medium", "high"})
SUPPORTED_MICROPHONE_SENSITIVITY = frozenset({"sensitive", "balanced", "noisy"})
SUPPORTED_DENSITIES = frozenset({"comfortable", "compact"})


@dataclass(frozen=True, slots=True)
class AppearanceSettings:
    theme: str = "dark"
    font_scale: float = 1.0
    compact_mode: bool = False
    reduce_motion: bool = False
    density: str = "comfortable"
    sidebar_collapsed: bool = False
    right_panel_visible: bool = True
    right_panel_section: str = "tools"
    right_panel_width: int = 320
    message_width: int = 820
    settings_last_section: int = 0


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
    input_sensitivity: str = "balanced"
    calibrated_noise_threshold: float | None = None


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
    window_x: int | None = None
    window_y: int | None = None
    window_width: int = 1440
    window_height: int = 900
    window_maximized: bool = False


@dataclass(frozen=True, slots=True)
class AgentUserSettings:
    agent_mode_enabled: bool = False
    max_agent_steps: int = 8
    max_agent_replans: int = 1
    auto_start_read_only_plans: bool = False
    always_show_plan: bool = True
    always_confirm_persistent_steps: bool = True
    speak_agent_progress: bool = False
    notify_agent_completion: bool = True
    speak_important_agent_events: bool = True
    speak_agent_completion: bool = True
    speak_agent_approvals: bool = True
    show_task_template_suggestions: bool = True
    notify_interrupted_tasks_on_startup: bool = True
    agent_history_retention_days: int | None = 30


@dataclass(frozen=True, slots=True)
class CodexUserSettings:
    bridge_enabled: bool = False
    cli_executable_path: str = ""
    auto_detect_cli: bool = True
    default_task_timeout_seconds: int = 300
    read_only_default: bool = True
    modification_confirmation: bool = True
    remembered_workspaces: tuple[str, ...] = ()
    default_approval_behavior: str = "always_ask"
    automatic_analysis_suggestions: bool = True
    history_retention_days: int | None = 30
    privacy_mode: str = "metadata_only"
    approval_enforced: bool = True
    workspace_restriction_enforced: bool = True
    secret_filtering_enforced: bool = True
    audit_logging_enforced: bool = True
    candidate_source: str = "unknown"
    session_retention_days: int = 30
    resume_enabled: bool = True
    diff_review_required: bool = True
    diff_max_size_kb: int = 1024
    diagnostics_verbosity: str = "standard"
    last_cli_health_check: str = ""


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
    agent: AgentUserSettings = AgentUserSettings()
    codex: CodexUserSettings = CodexUserSettings()

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("Unsupported user settings schema version")
        if self.appearance.theme not in SUPPORTED_THEMES:
            raise ValueError("Unsupported appearance theme")
        if not 0.85 <= self.appearance.font_scale <= 1.35:
            raise ValueError("Appearance font scale must be between 0.85 and 1.35")
        if self.appearance.density not in SUPPORTED_DENSITIES:
            raise ValueError("Unsupported interface density")
        if self.appearance.right_panel_section not in {"tools", "memory", "agent", "codex", "voice", "vision", "system"}:
            raise ValueError("Unsupported right panel section")
        if not 300 <= self.appearance.right_panel_width <= 360:
            raise ValueError("Right panel width must be between 300 and 360")
        if not 720 <= self.appearance.message_width <= 900:
            raise ValueError("Message width must be between 720 and 900")
        if not 0 <= self.appearance.settings_last_section <= 9:
            raise ValueError("Settings section index is outside safe bounds")
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
        if self.speech.input_sensitivity not in SUPPORTED_MICROPHONE_SENSITIVITY:
            raise ValueError("Unsupported microphone sensitivity")
        if self.speech.calibrated_noise_threshold is not None and not 0.004 <= self.speech.calibrated_noise_threshold <= 0.25:
            raise ValueError("Calibrated microphone threshold must be between 0.004 and 0.25")
        if self.models.keep_alive not in SUPPORTED_KEEP_ALIVE:
            raise ValueError("Unsupported model keep-alive")
        if not 32 <= self.models.max_output_tokens <= 8192:
            raise ValueError("Maximum output tokens must be between 32 and 8192")
        if not 1000 <= self.models.context_budget <= 100000:
            raise ValueError("Context budget must be between 1000 and 100000")
        if self.system.close_behavior not in SUPPORTED_CLOSE_BEHAVIORS:
            raise ValueError("Unsupported close behavior")
        if not 720 <= self.system.window_width <= 7680 or not 560 <= self.system.window_height <= 4320:
            raise ValueError("Saved window size is outside safe bounds")
        if self.live_vision.default_source not in SUPPORTED_LIVE_VISION_SOURCES:
            raise ValueError("Unsupported live vision source")
        if self.live_vision.change_sensitivity not in SUPPORTED_CHANGE_SENSITIVITY:
            raise ValueError("Unsupported live vision sensitivity")
        if not 3 <= self.agent.max_agent_steps <= 12:
            raise ValueError("Agent maximum steps must be between 3 and 12")
        if not 0 <= self.agent.max_agent_replans <= 1:
            raise ValueError("Agent maximum replans must be between 0 and 1")
        if not self.agent.always_confirm_persistent_steps:
            raise ValueError("Persistent Agent approval cannot be disabled")
        if self.agent.agent_history_retention_days not in {7, 30, 90, None}:
            raise ValueError("Unsupported Agent history retention")
        if self.codex.default_approval_behavior != "always_ask":
            raise ValueError("Codex approval cannot be disabled")
        if self.codex.history_retention_days not in {7, 30, 90, None}:
            raise ValueError("Unsupported Codex history retention")
        if not 15 <= self.codex.default_task_timeout_seconds <= 3600:
            raise ValueError("Codex task timeout must be between 15 and 3600 seconds")
        if not self.codex.modification_confirmation:
            raise ValueError("Codex modification confirmation cannot be disabled")
        if self.codex.privacy_mode != "metadata_only":
            raise ValueError("Codex history must remain metadata-only")
        if not all((self.codex.approval_enforced, self.codex.workspace_restriction_enforced,
                    self.codex.secret_filtering_enforced, self.codex.audit_logging_enforced)):
            raise ValueError("Codex safety controls cannot be disabled")
        if self.codex.session_retention_days not in {7, 30, 90}:
            raise ValueError("Unsupported Codex session retention")
        if not self.codex.diff_review_required:
            raise ValueError("Codex diff review cannot be disabled")
        if not 64 <= self.codex.diff_max_size_kb <= 4096:
            raise ValueError("Codex diff size limit is outside safe bounds")
        if self.codex.diagnostics_verbosity not in {"standard", "detailed"}:
            raise ValueError("Unsupported Codex diagnostics verbosity")
        if len(self.codex.candidate_source) > 80 or len(self.codex.last_cli_health_check) > 80:
            raise ValueError("Codex health metadata exceeds safe bounds")
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
                "density": self.appearance.density,
                "sidebar_collapsed": self.appearance.sidebar_collapsed,
                "right_panel_visible": self.appearance.right_panel_visible,
                "right_panel_section": self.appearance.right_panel_section,
                "right_panel_width": self.appearance.right_panel_width,
                "message_width": self.appearance.message_width,
                "settings_last_section": self.appearance.settings_last_section,
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
                "input_sensitivity": self.speech.input_sensitivity,
                "calibrated_noise_threshold": self.speech.calibrated_noise_threshold,
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
                "window_x": self.system.window_x,
                "window_y": self.system.window_y,
                "window_width": self.system.window_width,
                "window_height": self.system.window_height,
                "window_maximized": self.system.window_maximized,
            },
            "agent": {
                "agent_mode_enabled": self.agent.agent_mode_enabled,
                "max_agent_steps": self.agent.max_agent_steps,
                "max_agent_replans": self.agent.max_agent_replans,
                "auto_start_read_only_plans": self.agent.auto_start_read_only_plans,
                "always_show_plan": self.agent.always_show_plan,
                "always_confirm_persistent_steps": True,
                "speak_agent_progress": self.agent.speak_agent_progress,
                "notify_agent_completion": self.agent.notify_agent_completion,
                "speak_important_agent_events": self.agent.speak_important_agent_events,
                "speak_agent_completion": self.agent.speak_agent_completion,
                "speak_agent_approvals": self.agent.speak_agent_approvals,
                "show_task_template_suggestions": self.agent.show_task_template_suggestions,
                "notify_interrupted_tasks_on_startup": self.agent.notify_interrupted_tasks_on_startup,
                "agent_history_retention_days": self.agent.agent_history_retention_days,
            },
            "codex": {
                "bridge_enabled": self.codex.bridge_enabled,
                "cli_executable_path": self.codex.cli_executable_path,
                "auto_detect_cli": self.codex.auto_detect_cli,
                "default_task_timeout_seconds": self.codex.default_task_timeout_seconds,
                "read_only_default": self.codex.read_only_default,
                "modification_confirmation": True,
                "remembered_workspaces": list(self.codex.remembered_workspaces),
                "default_approval_behavior": "always_ask",
                "automatic_analysis_suggestions": self.codex.automatic_analysis_suggestions,
                "history_retention_days": self.codex.history_retention_days,
                "privacy_mode": "metadata_only",
                "approval_enforced": True,
                "workspace_restriction_enforced": True,
                "secret_filtering_enforced": True,
                "audit_logging_enforced": True,
                "candidate_source": self.codex.candidate_source,
                "session_retention_days": self.codex.session_retention_days,
                "resume_enabled": self.codex.resume_enabled,
                "diff_review_required": True,
                "diff_max_size_kb": self.codex.diff_max_size_kb,
                "diagnostics_verbosity": self.codex.diagnostics_verbosity,
                "last_cli_health_check": self.codex.last_cli_health_check,
            },
        }

    @classmethod
    def from_dict(cls, raw: object) -> "UserSettings":
        """Parse known fields and use safe defaults for missing or invalid values."""
        if not isinstance(raw, dict):
            return cls()
        if raw.get("schema_version") not in (None, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, SCHEMA_VERSION):
            return cls()
        defaults = cls()
        appearance = _section(raw, "appearance")
        general = _section(raw, "general")
        models = _section(raw, "models")
        speech = _section(raw, "speech")
        vision = _section(raw, "vision")
        live_vision = _section(raw, "live_vision")
        system = _section(raw, "system")
        agent = _section(raw, "agent")
        codex = _section(raw, "codex")
        return cls(
            appearance=AppearanceSettings(
                theme=_choice(appearance, "theme", defaults.appearance.theme, SUPPORTED_THEMES),
                font_scale=_bounded_float(appearance, "font_scale", defaults.appearance.font_scale, 0.85, 1.35),
                compact_mode=_bool(appearance, "compact_mode", defaults.appearance.compact_mode),
                reduce_motion=_bool(appearance, "reduce_motion", defaults.appearance.reduce_motion),
                density=_choice(appearance, "density", defaults.appearance.density, SUPPORTED_DENSITIES),
                sidebar_collapsed=_bool(appearance, "sidebar_collapsed", defaults.appearance.sidebar_collapsed),
                right_panel_visible=_bool(appearance, "right_panel_visible", defaults.appearance.right_panel_visible),
                right_panel_section=_choice(
                    appearance,
                    "right_panel_section",
                    defaults.appearance.right_panel_section,
                    {"tools", "memory", "agent", "codex", "voice", "vision", "system"},
                ),
                right_panel_width=_bounded_int(appearance, "right_panel_width", defaults.appearance.right_panel_width, 300, 360),
                message_width=_bounded_int(appearance, "message_width", defaults.appearance.message_width, 720, 900),
                settings_last_section=_bounded_int(appearance, "settings_last_section", defaults.appearance.settings_last_section, 0, 9),
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
                input_sensitivity=_choice(speech, "input_sensitivity", defaults.speech.input_sensitivity, SUPPORTED_MICROPHONE_SENSITIVITY),
                calibrated_noise_threshold=_optional_bounded_float(speech, "calibrated_noise_threshold", 0.004, 0.25),
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
                window_x=_optional_signed_int(system, "window_x", -10000, 10000),
                window_y=_optional_signed_int(system, "window_y", -10000, 10000),
                window_width=_bounded_int(system, "window_width", defaults.system.window_width, 720, 7680),
                window_height=_bounded_int(system, "window_height", defaults.system.window_height, 560, 4320),
                window_maximized=_bool(system, "window_maximized", defaults.system.window_maximized),
            ),
            agent=AgentUserSettings(
                agent_mode_enabled=_bool(agent, "agent_mode_enabled", defaults.agent.agent_mode_enabled),
                max_agent_steps=_bounded_int(agent, "max_agent_steps", defaults.agent.max_agent_steps, 3, 12),
                max_agent_replans=_bounded_int(agent, "max_agent_replans", defaults.agent.max_agent_replans, 0, 1),
                auto_start_read_only_plans=_bool(agent, "auto_start_read_only_plans", defaults.agent.auto_start_read_only_plans),
                always_show_plan=_bool(agent, "always_show_plan", defaults.agent.always_show_plan),
                always_confirm_persistent_steps=True,
                speak_agent_progress=_bool(agent, "speak_agent_progress", defaults.agent.speak_agent_progress),
                notify_agent_completion=_bool(agent, "notify_agent_completion", defaults.agent.notify_agent_completion),
                speak_important_agent_events=_bool(agent, "speak_important_agent_events", defaults.agent.speak_important_agent_events),
                speak_agent_completion=_bool(agent, "speak_agent_completion", defaults.agent.speak_agent_completion),
                speak_agent_approvals=_bool(agent, "speak_agent_approvals", defaults.agent.speak_agent_approvals),
                show_task_template_suggestions=_bool(agent, "show_task_template_suggestions", defaults.agent.show_task_template_suggestions),
                notify_interrupted_tasks_on_startup=_bool(agent, "notify_interrupted_tasks_on_startup", defaults.agent.notify_interrupted_tasks_on_startup),
                agent_history_retention_days=_history_retention(agent, defaults.agent.agent_history_retention_days),
            ),
            codex=CodexUserSettings(
                bridge_enabled=_bool(codex, "bridge_enabled", defaults.codex.bridge_enabled),
                cli_executable_path=_safe_string(
                    codex, "cli_executable_path", defaults.codex.cli_executable_path, 500),
                auto_detect_cli=_bool(codex, "auto_detect_cli", defaults.codex.auto_detect_cli),
                default_task_timeout_seconds=_bounded_int(
                    codex, "default_task_timeout_seconds",
                    defaults.codex.default_task_timeout_seconds, 15, 3600),
                read_only_default=_bool(codex, "read_only_default", defaults.codex.read_only_default),
                modification_confirmation=True,
                remembered_workspaces=_safe_string_tuple(codex, "remembered_workspaces"),
                default_approval_behavior="always_ask",
                automatic_analysis_suggestions=_bool(
                    codex, "automatic_analysis_suggestions", defaults.codex.automatic_analysis_suggestions),
                history_retention_days=_codex_history_retention(codex, defaults.codex.history_retention_days),
                privacy_mode="metadata_only",
                approval_enforced=True,
                workspace_restriction_enforced=True,
                secret_filtering_enforced=True,
                audit_logging_enforced=True,
                candidate_source=_safe_string(
                    codex, "candidate_source", defaults.codex.candidate_source, 80),
                session_retention_days=_choice_int(
                    codex, "session_retention_days", defaults.codex.session_retention_days,
                    {7, 30, 90}),
                resume_enabled=_bool(codex, "resume_enabled", defaults.codex.resume_enabled),
                diff_review_required=True,
                diff_max_size_kb=_bounded_int(
                    codex, "diff_max_size_kb", defaults.codex.diff_max_size_kb, 64, 4096),
                diagnostics_verbosity=_choice(
                    codex, "diagnostics_verbosity", defaults.codex.diagnostics_verbosity,
                    {"standard", "detailed"}),
                last_cli_health_check=_safe_string(
                    codex, "last_cli_health_check", defaults.codex.last_cli_health_check, 80),
            ),
        )


def _section(raw: dict[str, Any], name: str) -> dict[str, Any]:
    value = raw.get(name)
    return value if isinstance(value, dict) else {}


def _bool(section: dict[str, Any], key: str, default: bool) -> bool:
    value = section.get(key)
    return value if isinstance(value, bool) else default


def _history_retention(section: dict[str, Any], default: int | None) -> int | None:
    value = section.get("agent_history_retention_days", default)
    return value if value in {7, 30, 90, None} else default


def _codex_history_retention(section: dict[str, Any], default: int | None) -> int | None:
    value = section.get("history_retention_days", default)
    return value if value in {7, 30, 90, None} else default


def _safe_string_tuple(section: dict[str, Any], key: str) -> tuple[str, ...]:
    value = section.get(key, ())
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(item.strip()[:500] for item in value[:50]
                 if isinstance(item, str) and item.strip())


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


def _optional_bounded_float(section: dict[str, Any], key: str, minimum: float, maximum: float) -> float | None:
    value = section.get(key)
    if isinstance(value, (int, float)) and not isinstance(value, bool) and minimum <= value <= maximum:
        return float(value)
    return None


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


def _optional_signed_int(section: dict[str, Any], key: str, minimum: int, maximum: int) -> int | None:
    value = section.get(key)
    return value if isinstance(value, int) and not isinstance(value, bool) and minimum <= value <= maximum else None


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
