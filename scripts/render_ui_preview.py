"""Render deterministic offscreen Lina UI previews for visual QA."""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PIL import Image
from PySide6.QtGui import QFontDatabase, QImage
from PySide6.QtWidgets import QApplication

from lina.brain.model_provider import ModelResponse
from lina.conversations.models import ConversationSession
from lina.interfaces.qt.main_window import LinaMainWindow
from lina.interfaces.qt.settings_dialog import SettingsDialog
from lina.interfaces.qt.theme import build_stylesheet
from lina.services.conversation_models import ConversationResult
from lina.settings.repository import UserSettingsRepository
from lina.settings.service import UserSettingsService


class PreviewConversationService:
    conversation_history_service = None

    def handle_input(self, value):
        return ConversationResult(ModelResponse("Önizleme yanıtı"))


def render(output: Path, width: int, height: int, surface: str) -> None:
    application = QApplication.instance() or QApplication([])
    font_path = Path("C:/Windows/Fonts/segoeui.ttf")
    if font_path.exists():
        QFontDatabase.addApplicationFont(str(font_path))
    application.setStyleSheet(build_stylesheet("Segoe UI", "dark", 1.0))
    if surface == "settings":
        service = UserSettingsService(UserSettingsRepository(output.parent / "_qa-settings.json"))
        window = SettingsDialog(service)
        window.resize(width, height)
    else:
        window = LinaMainWindow(PreviewConversationService())
        window.resize(width, height)
        now = datetime.now(timezone.utc)
        sessions = (
            ConversationSession(1, "Lina arayüz fikirleri", now, now, now),
            ConversationSession(2, "Bugünkü plan", now - timedelta(hours=2), now, now - timedelta(hours=2)),
            ConversationSession(3, "Ürün yol haritası", now - timedelta(days=1), now, now - timedelta(days=1)),
            ConversationSession(4, "Kod inceleme desteği", now - timedelta(days=2), now, now - timedelta(days=2)),
        )
        window._sidebar.set_sessions(sessions, active_id=1)
        window._hide_welcome_state()
        window._set_session_title("Lina arayüz fikirleri")
        window._append_user_message("Lina arayüzünü daha sade ve profesyonel yapalım.", created_at=now)
        window._append_assistant_message(
            "Ana çalışma alanını sohbet merkezli tutup araçları gerektiğinde açabiliriz. "
            "Sidebar, mesaj yüzeyleri ve composer aynı spacing ritmini kullanmalı.",
            created_at=now,
        )
    window.show()
    application.processEvents()
    output.parent.mkdir(parents=True, exist_ok=True)
    image = window.grab().toImage().convertToFormat(QImage.Format.Format_RGBA8888)
    raw = bytes(image.bits())
    preview = Image.frombytes(
        "RGBA", (image.width(), image.height()), raw,
        "raw", "RGBA", image.bytesPerLine(), 1,
    )
    preview.save(output)
    if isinstance(window, LinaMainWindow):
        window._force_exit = True
    window.close()
    application.processEvents()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--width", type=int, default=1440)
    parser.add_argument("--height", type=int, default=900)
    parser.add_argument("--surface", choices=("main", "settings"), default="main")
    arguments = parser.parse_args()
    render(arguments.output, arguments.width, arguments.height, arguments.surface)


if __name__ == "__main__":
    main()
