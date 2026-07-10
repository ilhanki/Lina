"""Application bootstrap helpers for Lina entry points."""

from dataclasses import dataclass
from pathlib import Path

from lina.brain.brain import Brain
from lina.brain.context_manager import ContextManager
from lina.core.application import LinaApplication
from lina.core.context import ApplicationContext
from lina.core.logging import configure_logging
from lina.core.paths import AppPaths
from lina.core.settings import SpeechSettings, load_settings
from lina.files.file_access_service import FileAccessService
from lina.integrations.ollama_provider import OllamaProvider
from lina.memory.repository import MemoryRepository
from lina.memory.service import MemoryService
from lina.services.conversation_service import ConversationService
from lina.services.git_context_service import GitContextService
from lina.services.model_diagnostics_service import ModelDiagnosticsService
from lina.services.project_context_service import ProjectContextService
from lina.services.tool_execution_service import ToolExecutionService
from lina.speech.audio_recorder import NoOpAudioRecorder, SoundDeviceAudioRecorder
from lina.speech.faster_whisper_provider import FasterWhisperSTTProvider
from lina.speech.providers import NoOpSTTProvider, NoOpTTSProvider
from lina.speech.service import SpeechService
from lina.tools.builtin import CurrentTimeTool, EchoTool
from lina.tools.registry import ToolRegistry


@dataclass(frozen=True)
class ApplicationServices:
    """Services needed by Lina entry points."""

    application: LinaApplication
    conversation_service: ConversationService
    diagnostics_service: ModelDiagnosticsService
    speech_service: SpeechService


def create_application_services(
    config_path: Path,
    project_root: Path,
) -> ApplicationServices:
    """Create core application services for an entry point."""
    settings = load_settings(config_path)
    paths = AppPaths.from_project_root(project_root)
    logger = configure_logging(settings.logging.level)
    context = ApplicationContext(settings=settings, paths=paths, logger=logger)
    application = LinaApplication(context=context)

    provider = OllamaProvider(
        base_url=settings.ollama.base_url,
        model=settings.ollama.default_model,
        timeout=settings.ollama.request_timeout,
    )
    brain = Brain(model_provider=provider)
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
    file_access_service = FileAccessService(project_root=project_root)
    context_manager = ContextManager(
        project_context_service=project_context_service,
        git_context_service=git_context_service,
        memory_service=memory_service,
        history_limit=settings.runtime.conversation_history_limit,
        memory_context_max_items=settings.memory.max_context_items,
        memory_context_max_characters=settings.memory.max_context_characters,
    )
    tool_registry = ToolRegistry()
    tool_registry.register(EchoTool())
    tool_registry.register(CurrentTimeTool())
    tool_execution_service = ToolExecutionService(tool_registry=tool_registry)
    conversation_service = ConversationService(
        brain=brain,
        context_manager=context_manager,
        tool_execution_service=tool_execution_service,
        memory_service=memory_service,
        file_access_service=file_access_service,
        history_limit=settings.runtime.conversation_history_limit,
    )
    diagnostics_service = ModelDiagnosticsService(
        base_url=settings.ollama.base_url,
        model=settings.ollama.default_model,
        timeout=min(settings.ollama.request_timeout, 5.0),
    )
    speech_service = _create_speech_service(settings.speech)

    return ApplicationServices(
        application=application,
        conversation_service=conversation_service,
        diagnostics_service=diagnostics_service,
        speech_service=speech_service,
    )


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
