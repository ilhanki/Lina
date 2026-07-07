"""Lina desktop GUI entry point."""

from collections.abc import Callable
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from lina.core.application import ApplicationState
from lina.core.bootstrap import create_application_services
from lina.services.conversation_service import ConversationService


def run_gui_application(
    config_path: Path = PROJECT_ROOT / "config" / "default.toml",
    project_root: Path = PROJECT_ROOT,
    gui_launcher: Callable[[ConversationService], None] | None = None,
) -> None:
    services = create_application_services(
        config_path=config_path,
        project_root=project_root,
    )
    launcher = gui_launcher or _launch_tkinter_gui

    services.application.start()
    try:
        launcher(services.conversation_service)
    finally:
        if services.application.state is ApplicationState.RUNNING:
            services.application.stop()


def _launch_tkinter_gui(conversation_service: ConversationService) -> None:
    from lina.interfaces.gui import LinaGui

    gui = LinaGui(conversation_service=conversation_service)
    gui.run()


def main() -> None:
    run_gui_application()


if __name__ == "__main__":
    main()
