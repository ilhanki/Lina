from pathlib import Path

from gui import run_gui_application
from lina.services.conversation_service import ConversationService


def test_run_gui_application_launches_gui_with_conversation_service(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)
    launched_services: list[ConversationService] = []

    run_gui_application(
        config_path=config_path,
        project_root=tmp_path,
        gui_launcher=launched_services.append,
    )

    assert len(launched_services) == 1
    assert isinstance(launched_services[0], ConversationService)


def _write_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "default.toml"
    config_path.write_text(
        """
        [app]
        name = "Lina"
        environment = "test"

        [logging]
        level = "INFO"

        [paths]
        data = "data"
        logs = "logs"
        models = "models"
        cache = "cache"

        [ollama]
        base_url = "http://localhost:11434"
        default_model = "llama3"
        """,
        encoding="utf-8",
    )
    return config_path
