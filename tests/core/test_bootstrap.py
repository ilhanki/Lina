from pathlib import Path

from lina.core.application import ApplicationState
from lina.core.bootstrap import create_application_services
from lina.services.conversation_service import ConversationService


def test_create_application_services_creates_application_and_conversation_service(
    tmp_path: Path,
) -> None:
    config_path = _write_config(tmp_path)

    services = create_application_services(
        config_path=config_path,
        project_root=tmp_path,
    )

    assert services.application.state is ApplicationState.INITIALIZED
    assert isinstance(services.conversation_service, ConversationService)


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
