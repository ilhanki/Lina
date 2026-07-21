from pathlib import Path
import tomllib

from lina.interfaces.qt.main_window import APP_VERSION as QT_APP_VERSION
from lina.interfaces.gui import APP_VERSION as TK_APP_VERSION
from lina.version import __version__


def test_v0140_alpha_version_contract() -> None:
    root = Path(__file__).resolve().parents[1]
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))

    assert project["project"]["version"] == __version__ == "0.14.0a0"
    assert QT_APP_VERSION == TK_APP_VERSION == "v0.14.0-alpha"
