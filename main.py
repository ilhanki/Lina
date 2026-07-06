"""Lina application entry point."""

from pathlib import Path
import sys
from typing import TextIO


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from lina.brain.brain import Brain
from lina.core.application import ApplicationState, LinaApplication
from lina.core.context import ApplicationContext
from lina.core.logging import configure_logging
from lina.core.paths import AppPaths
from lina.core.settings import load_settings
from lina.integrations.ollama_provider import OllamaProvider
from lina.interfaces.cli import LinaCli
from lina.services.conversation_service import ConversationService


def run_application(
    config_path: Path = PROJECT_ROOT / "config" / "default.toml",
    project_root: Path = PROJECT_ROOT,
    input_stream: TextIO = sys.stdin,
    output_stream: TextIO = sys.stdout,
) -> None:
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
    conversation_service = ConversationService(brain=brain)
    cli = LinaCli(
        conversation_service=conversation_service,
        input_stream=input_stream,
        output_stream=output_stream,
    )

    application.start()
    try:
        cli.run()
    finally:
        if application.state is ApplicationState.RUNNING:
            application.stop()


def main() -> None:
    run_application()


if __name__ == "__main__":
    main()

