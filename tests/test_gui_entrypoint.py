from pathlib import Path

import lina.interfaces.qt.application as qt_application_module
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


def test_default_gui_launcher_uses_pyside6_application(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config_path = _write_config(tmp_path)
    launched_services: list[ApplicationServices] = []

    def fake_run_qt_application(services: ApplicationServices) -> int:
        launched_services.append(services)
        return 0

    monkeypatch.setattr(
        qt_application_module,
        "run_qt_application",
        fake_run_qt_application,
    )

    run_gui_application(config_path=config_path, project_root=tmp_path)

    assert len(launched_services) == 1
    assert launched_services[0].conversation_service is not None
    assert launched_services[0].diagnostics_service is not None
    assert launched_services[0].speech_service.is_stt_available() is False


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
