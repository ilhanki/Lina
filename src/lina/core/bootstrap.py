"""Application bootstrap helpers for Lina entry points."""

from dataclasses import dataclass
from pathlib import Path

from lina.brain.brain import Brain
from lina.core.application import LinaApplication
from lina.core.context import ApplicationContext
from lina.core.logging import configure_logging
from lina.core.paths import AppPaths
from lina.core.settings import load_settings
from lina.integrations.ollama_provider import OllamaProvider
from lina.services.conversation_service import ConversationService
from lina.services.project_context_service import ProjectContextService
from lina.services.tool_execution_service import ToolExecutionService
from lina.tools.builtin import CurrentTimeTool, EchoTool
from lina.tools.registry import ToolRegistry


@dataclass(frozen=True)
class ApplicationServices:
    """Services needed by Lina entry points."""

    application: LinaApplication
    conversation_service: ConversationService


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
    )
    brain = Brain(model_provider=provider)
    project_context_service = ProjectContextService(project_root=project_root)
    tool_registry = ToolRegistry()
    tool_registry.register(EchoTool())
    tool_registry.register(CurrentTimeTool())
    tool_execution_service = ToolExecutionService(tool_registry=tool_registry)
    conversation_service = ConversationService(
        brain=brain,
        project_context_service=project_context_service,
        tool_execution_service=tool_execution_service,
    )

    return ApplicationServices(
        application=application,
        conversation_service=conversation_service,
    )
