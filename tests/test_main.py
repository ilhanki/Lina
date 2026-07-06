from io import StringIO
from pathlib import Path

from main import run_application


def test_run_application_starts_cli_with_config(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)
    output_stream = StringIO()

    run_application(
        config_path=config_path,
        project_root=tmp_path,
        input_stream=StringIO("quit\n"),
        output_stream=output_stream,
    )

    output = output_stream.getvalue()
    assert "Lina v0.1.0" in output
    assert "Merhaba İlhan." in output
    assert "Hazırım." in output


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

