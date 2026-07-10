from pathlib import Path

import lina.interfaces.gui as gui_module
from gui import run_gui_application
from lina.core.bootstrap import ApplicationServices
from lina.services.conversation_service import ConversationService


def test_run_gui_application_launches_gui_with_conversation_service(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)
    launched_services: list[ApplicationServices] = []

    run_gui_application(
        config_path=config_path,
        project_root=tmp_path,
        gui_launcher=launched_services.append,
    )

    assert len(launched_services) == 1
    assert isinstance(launched_services[0].conversation_service, ConversationService)
    assert launched_services[0].speech_service.is_stt_available() is False


def test_default_gui_launcher_receives_bootstrapped_speech_service(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config_path = _write_config(tmp_path)
    created_arguments = {}

    class FakeGui:
        def __init__(self, **kwargs) -> None:
            created_arguments.update(kwargs)

        def run(self) -> None:
            created_arguments["run_called"] = True

    monkeypatch.setattr(gui_module, "LinaGui", FakeGui)

    run_gui_application(config_path=config_path, project_root=tmp_path)

    assert created_arguments["conversation_service"] is not None
    assert created_arguments["diagnostics_service"] is not None
    assert created_arguments["speech_service"].is_stt_available() is False
    assert created_arguments["run_called"] is True


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
