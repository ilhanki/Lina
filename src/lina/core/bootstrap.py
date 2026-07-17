"""Application bootstrap helpers for Lina entry points."""

from dataclasses import dataclass
from pathlib import Path
import threading

from lina.brain.brain import Brain
from lina.brain.conversation_context import ConversationContext
from lina.brain.context_manager import ContextManager
from lina.brain.prompt_builder import PromptBuilder
from lina.brain.prompts import VISION_SYSTEM_PROMPT
from lina.brain.routing.router import IntentRouter
from lina.brain.routing.tools import build_safe_tool_registry
from lina.agent import AgentController, AgentExecutor, AgentPlanner, AgentPolicy, AgentSessionRepository, AgentVerifier
from lina.agent.templates import build_builtin_template_registry
from lina.core.application import LinaApplication
from lina.core.context import ApplicationContext
from lina.core.logging import configure_logging
from lina.core.paths import AppPaths
from lina.core.settings import SpeechSettings, load_settings
from lina.conversations.repository import ConversationRepository
from lina.conversations.service import ConversationHistoryService
from lina.files.file_access_service import FileAccessService
from lina.integrations.ollama_provider import OllamaProvider
from lina.memory.repository import MemoryRepository
from lina.memory.service import MemoryService
from lina.services.local_storage_service import LocalStorageService
from lina.notifications.repository import NotificationRepository
from lina.notifications.service import NotificationService
from lina.services.conversation_service import ConversationService
from lina.services.git_context_service import GitContextService
from lina.services.model_diagnostics_service import (
    ModelDiagnosticsService,
    VisionDiagnosticsService,
    VisionStatus,
)
from lina.services.project_context_service import ProjectContextService
from lina.services.tool_execution_service import ToolExecutionService
from lina.speech.audio_recorder import NoOpAudioRecorder, SoundDeviceAudioRecorder
from lina.speech.faster_whisper_provider import FasterWhisperSTTProvider
from lina.speech.providers import NoOpSTTProvider, NoOpTTSProvider
from lina.speech.service import SpeechService
from lina.voice.controller import VoiceController
from lina.voice.hands_free import HandsFreeConversationService
from lina.voice.models import VoiceSettings
from lina.voice.playback import AudioPlaybackService
from lina.voice.tts_provider import QtWindowsTTSProvider
from lina.voice.wake_audio import SoundDeviceWakeAudioSource
from lina.voice.wake_word import STTWakeWordDetector
from lina.inference.service import InferenceDiagnosticsService, ModelLifecycleService
from lina.settings.repository import UserSettingsRepository, default_user_settings_path
from lina.settings.service import UserSettingsService
from lina.tools.builtin import CurrentTimeTool, EchoTool
from lina.tools.registry import ToolRegistry
from lina.vision.live import LiveVisionController
from lina.vision.models import ImageAttachment


@dataclass(frozen=True)
class ApplicationServices:
    """Services needed by Lina entry points."""

    application: LinaApplication
    conversation_service: ConversationService
    diagnostics_service: ModelDiagnosticsService
    vision_diagnostics_service: VisionDiagnosticsService
    speech_service: SpeechService
    conversation_history_service: ConversationHistoryService | None = None
    user_settings_service: UserSettingsService | None = None
    notification_service: NotificationService | None = None
    intent_router: IntentRouter | None = None
    voice_controller: VoiceController | None = None
    inference_diagnostics_service: InferenceDiagnosticsService | None = None
    model_lifecycle_service: ModelLifecycleService | None = None
    hands_free_service: HandsFreeConversationService | None = None
    live_vision_controller: LiveVisionController | None = None
    agent_controller: AgentController | None = None
    memory_service: MemoryService | None = None
    local_storage_service: LocalStorageService | None = None


def create_application_services(
    config_path: Path,
    project_root: Path,
    user_settings_path: Path | None = None,
) -> ApplicationServices:
    """Create core application services for an entry point."""
    settings = load_settings(config_path)
    paths = AppPaths.from_project_root(project_root)
    logger = configure_logging(settings.logging.level)
    context = ApplicationContext(settings=settings, paths=paths, logger=logger)
    application = LinaApplication(context=context)

    user_settings_service = UserSettingsService(
        UserSettingsRepository(user_settings_path or default_user_settings_path())
    )
    user_preferences = user_settings_service.current

    provider = OllamaProvider(
        base_url=settings.ollama.base_url,
        model=user_preferences.models.text_model,
        timeout=settings.ollama.request_timeout,
        keep_alive=user_preferences.models.keep_alive,
        max_output_tokens=user_preferences.models.max_output_tokens,
        stream=True,
    )
    brain = Brain(model_provider=provider)
    vision_provider = OllamaProvider(
        base_url=settings.ollama.base_url,
        model=user_preferences.models.vision_model,
        timeout=settings.vision.request_timeout,
        max_image_bytes=settings.vision.max_image_bytes,
        keep_alive="0",
        max_output_tokens=user_preferences.models.max_output_tokens,
        stream=False,
    )
    vision_brain = Brain(
        model_provider=vision_provider,
        prompt_builder=PromptBuilder(system_prompt=VISION_SYSTEM_PROMPT),
    )
    project_context_service = ProjectContextService(
        project_root=project_root,
        max_characters_per_file=settings.runtime.project_context_max_characters,
    )
    git_context_service = GitContextService(project_root=project_root)
    memory_service = _create_memory_service(
        project_root=project_root,
        database_path=settings.memory.database_path,
        enabled=settings.memory.enabled,
    )
    local_storage_service = LocalStorageService((paths.data_dir, paths.cache_dir))
    conversation_history_service = _create_conversation_history_service(
        project_root=project_root,
        database_path=settings.conversations.database_path,
        enabled=settings.conversations.enabled,
        max_loaded_messages=settings.conversations.max_loaded_messages,
        model_history_messages=settings.conversations.model_history_messages,
    )
    file_access_service = FileAccessService(project_root=project_root)
    context_manager = ContextManager(
        project_context_service=project_context_service,
        git_context_service=git_context_service,
        memory_service=memory_service,
        history_limit=settings.runtime.conversation_history_limit,
        memory_context_max_items=settings.memory.max_context_items,
        memory_context_max_characters=settings.memory.max_context_characters,
        context_character_budget=user_preferences.models.context_budget,
    )
    model_lifecycle_service = ModelLifecycleService(provider, vision_provider)
    tool_registry = ToolRegistry()
    tool_registry.register(EchoTool())
    tool_registry.register(CurrentTimeTool())
    tool_execution_service = ToolExecutionService(tool_registry=tool_registry)
    vision_diagnostics_service = VisionDiagnosticsService(
        base_url=settings.ollama.base_url,
        model=user_preferences.models.vision_model,
        enabled=settings.vision.enabled,
        timeout=min(settings.vision.request_timeout, 5.0),
    )
    conversation_service = ConversationService(
        brain=brain,
        context_manager=context_manager,
        tool_execution_service=tool_execution_service,
        memory_service=memory_service,
        file_access_service=file_access_service,
        vision_brain=vision_brain,
        vision_diagnostics_service=vision_diagnostics_service,
        consume_vision_attachment_on_success=(
            settings.vision.consume_attachment_on_success
        ),
        history_limit=settings.runtime.conversation_history_limit,
        conversation_history_service=conversation_history_service,
        model_lifecycle_service=model_lifecycle_service,
    )
    diagnostics_service = ModelDiagnosticsService(
        base_url=settings.ollama.base_url,
        model=user_preferences.models.text_model,
        timeout=min(settings.ollama.request_timeout, 5.0),
    )
    speech_service = _create_speech_service(settings.speech)
    user_settings_service.subscribe(
        lambda user_settings: _apply_user_model_settings(
            user_settings.models,
            provider,
            vision_provider,
            diagnostics_service,
            vision_diagnostics_service,
        )
    )
    tts_provider = QtWindowsTTSProvider()
    wake_audio_source = SoundDeviceWakeAudioSource(
        sample_rate=settings.speech.sample_rate,
        channels=settings.speech.channels,
        noise_threshold=settings.speech.silence_threshold,
        device_id=user_preferences.speech.microphone_device_id,
    )
    wake_word_detector = STTWakeWordDetector(
        speech_service.stt_provider,
        wake_audio_source,
        phrase=user_preferences.speech.wake_phrase,
    )
    voice_controller = VoiceController(
        AudioPlaybackService(tts_provider),
        wake_word=wake_word_detector,
        settings=VoiceSettings(
            enabled=user_preferences.speech.enabled,
            responses_enabled=user_preferences.speech.voice_responses_enabled,
            voice_id=user_preferences.speech.system_voice,
            rate=user_preferences.speech.speech_rate,
            volume=user_preferences.speech.volume,
            barge_in_enabled=user_preferences.speech.barge_in_enabled,
            hands_free_enabled=user_preferences.speech.hands_free_enabled,
            wake_word_enabled=user_preferences.speech.wake_word_enabled,
            wake_phrase=user_preferences.speech.wake_phrase,
            return_to_wake_listening=user_preferences.speech.return_to_wake_listening,
            voice_confirmation_enabled=user_preferences.speech.voice_confirmation_enabled,
            microphone_device_id=user_preferences.speech.microphone_device_id,
        ),
    )
    hands_free_service = HandsFreeConversationService(voice_controller, speech_service)
    def analyze_live_frame(frame, prompt: str) -> str:
        vision_status = vision_diagnostics_service.check_status()
        if vision_status.status is not VisionStatus.READY:
            if vision_status.status is VisionStatus.VISION_NOT_SUPPORTED:
                raise VisionRequestError(
                    "Seçili model görüntü analizi desteklemiyor. Ayarlardan bir vision modeli seç."
                )
            raise VisionRequestError("Vision modeli kullanılamıyor.")
        model_lifecycle_service.prepare_vision()
        try:
            attachment = ImageAttachment(
                mime_type="image/png",
                data=frame.data,
                width=frame.width,
                height=frame.height,
                captured_at=frame.captured_at,
                source=f"live_{frame.source.value}",
                display_name=frame.source_label or frame.source.value,
            )
            response = vision_brain.respond_with_image(
                ConversationContext(prompt, ()), attachment
            )
            return response.text
        finally:
            model_lifecycle_service.finish_vision()

    live_vision_controller = LiveVisionController(
        analyze_live_frame,
        speaker=voice_controller.speak_live_vision,
        cancel_analysis=model_lifecycle_service.cancel_active,
    )
    inference_diagnostics_service = InferenceDiagnosticsService(provider)
    if user_preferences.models.warm_up_enabled:
        threading.Thread(
            target=_warm_up_safely,
            args=(model_lifecycle_service,),
            name="lina-model-warmup",
            daemon=True,
        ).start()
    notification_service = NotificationService(NotificationRepository(project_root / "data" / "notifications.sqlite3"))
    safe_tool_registry = build_safe_tool_registry(notification_service, file_access_service, memory_service)
    intent_router = IntentRouter(
        safe_tool_registry,
        enabled_provider=lambda: user_settings_service.current.general.intent_routing_enabled,
    )
    agent_policy = AgentPolicy(
        max_steps=user_preferences.agent.max_agent_steps,
        max_replans=user_preferences.agent.max_agent_replans,
    )
    agent_repository = AgentSessionRepository(project_root / "data" / "agent-sessions.json")
    try:
        agent_repository.recover_interrupted()
        agent_repository.cleanup(user_preferences.agent.agent_history_retention_days)
    except (OSError, ValueError, TypeError):
        pass
    agent_controller = AgentController(
        AgentPlanner(agent_policy, template_registry=build_builtin_template_registry()),
        AgentExecutor(safe_tool_registry),
        AgentVerifier(),
        agent_policy,
        agent_repository,
        auto_start_read_only_plans=user_preferences.agent.auto_start_read_only_plans,
        always_show_plan=user_preferences.agent.always_show_plan,
    )

    return ApplicationServices(
        application=application,
        conversation_service=conversation_service,
        diagnostics_service=diagnostics_service,
        vision_diagnostics_service=vision_diagnostics_service,
        speech_service=speech_service,
        conversation_history_service=conversation_history_service,
        user_settings_service=user_settings_service,
        notification_service=notification_service,
        intent_router=intent_router,
        voice_controller=voice_controller,
        inference_diagnostics_service=inference_diagnostics_service,
        model_lifecycle_service=model_lifecycle_service,
        hands_free_service=hands_free_service,
        live_vision_controller=live_vision_controller,
        agent_controller=agent_controller,
        memory_service=memory_service,
        local_storage_service=local_storage_service,
    )


def _warm_up_safely(lifecycle: ModelLifecycleService) -> None:
    try:
        lifecycle.warm_up()
    except Exception:
        return


def _apply_user_model_settings(
    model_settings: object,
    provider: OllamaProvider,
    vision_provider: OllamaProvider,
    diagnostics_service: ModelDiagnosticsService,
    vision_diagnostics_service: VisionDiagnosticsService,
) -> None:
    """Apply user-selected model names to future provider requests."""
    text_model = str(getattr(model_settings, "text_model"))
    vision_model = str(getattr(model_settings, "vision_model"))
    provider.set_model(text_model)
    vision_provider.set_model(vision_model)
    provider.configure(
        str(getattr(model_settings, "keep_alive")),
        int(getattr(model_settings, "max_output_tokens")),
    )
    vision_provider.configure("0", int(getattr(model_settings, "max_output_tokens")))
    diagnostics_service.set_model(text_model)
    vision_diagnostics_service.set_model(vision_model)


def _create_memory_service(
    project_root: Path,
    database_path: str,
    enabled: bool,
) -> MemoryService | None:
    if not enabled:
        return None

    configured_path = Path(database_path)
    if configured_path.is_absolute():
        resolved_database_path = configured_path
    else:
        resolved_database_path = project_root / configured_path

    repository = MemoryRepository(resolved_database_path)
    return MemoryService(repository=repository)


def _create_conversation_history_service(
    project_root: Path,
    database_path: str,
    enabled: bool,
    max_loaded_messages: int,
    model_history_messages: int,
) -> ConversationHistoryService:
    if not enabled:
        return ConversationHistoryService(
            repository=None,
            enabled=False,
            max_loaded_messages=max_loaded_messages,
            model_history_messages=model_history_messages,
        )

    configured_path = Path(database_path)
    resolved_database_path = (
        configured_path if configured_path.is_absolute() else project_root / configured_path
    )
    repository = ConversationRepository(resolved_database_path)
    return ConversationHistoryService(
        repository=repository,
        enabled=True,
        max_loaded_messages=max_loaded_messages,
        model_history_messages=model_history_messages,
    )


def _create_speech_service(settings: SpeechSettings) -> SpeechService:
    if not settings.enabled or settings.stt_provider == "noop":
        return SpeechService(
            stt_provider=NoOpSTTProvider(),
            tts_provider=NoOpTTSProvider(),
            audio_recorder=NoOpAudioRecorder(),
        )

    recorder = SoundDeviceAudioRecorder(
        sample_rate=settings.sample_rate,
        channels=settings.channels,
        max_recording_seconds=settings.max_recording_seconds,
        silence_threshold=settings.silence_threshold,
        silence_duration_seconds=settings.silence_duration_seconds,
    )
    provider = FasterWhisperSTTProvider(
        model_size=settings.model_size,
        language=settings.language,
        device=settings.device,
        compute_type=settings.compute_type,
    )
    return SpeechService(
        stt_provider=provider,
        tts_provider=NoOpTTSProvider(),
        audio_recorder=recorder,
    )
