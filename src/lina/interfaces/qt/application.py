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
    user_settings = (
        services.user_settings_service.current
        if services.user_settings_service is not None
        else None
    )
    font_scale = user_settings.appearance.font_scale if user_settings else 1.0
    theme = user_settings.appearance.theme if user_settings else "dark"
    app.setFont(QFont(font_family, round(11 * font_scale)))
    app.setStyleSheet(build_stylesheet(font_family, theme=theme, font_scale=font_scale))
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
        notification_service=services.notification_service,
        intent_router=services.intent_router,
        voice_controller=services.voice_controller,
        inference_diagnostics_service=services.inference_diagnostics_service,
        model_lifecycle_service=services.model_lifecycle_service,
    )
    window.show()
    if (
        user_settings is not None
        and user_settings.system.start_minimized
        and window._tray_icon is not None
    ):
        window.hide()

    if not execute:
        return window
    return app.exec()
