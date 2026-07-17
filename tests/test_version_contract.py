from pathlib import Path
import tomllib

from lina.interfaces.qt.main_window import APP_VERSION as QT_APP_VERSION


def test_v0122_alpha_version_contract() -> None:
    root = Path(__file__).resolve().parents[1]
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))

    assert project["project"]["version"] == "0.12.2a0"
    assert QT_APP_VERSION == "v0.12.2-alpha"
