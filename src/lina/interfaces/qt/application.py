"""Application launcher for Lina's PySide6 interface."""

from __future__ import annotations

import sys

from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

from lina.core.bootstrap import ApplicationServices
from lina.interfaces.qt.main_window import BRANDING_ICON_PATH, LinaMainWindow
from lina.interfaces.qt.theme import build_stylesheet, resolve_font_family


def run_qt_application(
    services: ApplicationServices,
    execute: bool = True,
) -> int | LinaMainWindow:
    """Create and run Lina's PySide6 desktop application."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setApplicationName("Lina")
    app.setApplicationDisplayName("Lina")

    font_family = resolve_font_family()
    app.setFont(QFont(font_family, 11))
    app.setStyleSheet(build_stylesheet(font_family))
    if BRANDING_ICON_PATH.exists():
        icon = QIcon(str(BRANDING_ICON_PATH))
        if not icon.isNull():
            app.setWindowIcon(icon)

    window = LinaMainWindow(
        conversation_service=services.conversation_service,
        diagnostics_service=services.diagnostics_service,
        vision_diagnostics_service=services.vision_diagnostics_service,
        speech_service=services.speech_service,
        user_settings_service=services.user_settings_service,
    )
    window.show()

    if not execute:
        return window
    return app.exec()
