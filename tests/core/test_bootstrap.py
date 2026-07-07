import pytest
from pathlib import Path
from lina.core.bootstrap import create_application_services

def test_bootstrap_wires_services_correctly(tmp_path: Path) -> None:
    config_path = tmp_path / "settings.toml"
    config_path.write_text("""
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
request_timeout = 15.0

[runtime]
conversation_history_limit = 5
project_context_max_characters = 1000
    """, encoding="utf-8")

    services = create_application_services(config_path, tmp_path)

    assert services.application is not None
    assert services.conversation_service is not None
    assert services.diagnostics_service is not None
    assert services.conversation_service._history_limit == 5
    assert services.diagnostics_service._timeout == 5.0  # Min check in bootstrap
