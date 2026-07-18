from pathlib import Path

from lina.codex.transports.diagnostics import CodexCliInfo
from lina.interfaces.qt.codex_panel import CodexInspector


def test_panel_shows_cli_missing(qtbot) -> None:
    panel = CodexInspector()
    qtbot.addWidget(panel)
    panel.render(None, info=CodexCliInfo())
    assert "CLI bulunamadı" in panel.cli_status_label.text()
    assert not panel.login_button.isVisible()


def test_panel_shows_login_required_and_supported_device_auth(qtbot, tmp_path: Path) -> None:
    panel = CodexInspector()
    qtbot.addWidget(panel)
    panel.render(None, info=CodexCliInfo(
        tmp_path / "codex.exe", "1.2.3", True, False, supports_exec=True,
        supports_json=True, supports_device_auth=True,
    ))
    panel.show()
    assert "Oturum gerekli" in panel.cli_status_label.text()
    assert panel.login_button.isVisible()
    assert panel.device_login_button.isVisible()


def test_panel_shows_ready_and_general_auth_method_only(qtbot, tmp_path: Path) -> None:
    panel = CodexInspector()
    qtbot.addWidget(panel)
    panel.render(None, info=CodexCliInfo(
        tmp_path / "codex.exe", "1.2.3", True, True, "ChatGPT",
        supports_exec=True, supports_json=True,
    ))
    panel.show()
    assert "Hazır" in panel.cli_status_label.text()
    assert "ChatGPT" in panel.auth_status_label.text()
    assert panel.logout_button.isVisible()

