"""Theme and font helpers for Lina's PySide6 interface."""

from __future__ import annotations

from PySide6.QtGui import QFontDatabase


APP_BG = "#0f1117"
SIDEBAR_BG = "#0a0c11"
PANEL_BG = "#181c24"
COMPOSER_BG = "#1d222c"
ASSISTANT_BUBBLE = "#222833"
USER_BUBBLE = "#315fe8"
TEXT_PRIMARY = "#f5f7fb"
TEXT_SECONDARY = "#d4dae4"
TEXT_MUTED = "#aab4c3"
ACCENT = "#5f86ff"
ACCENT_HOVER = "#7396ff"
BORDER = "#343c49"
SUCCESS = "#65d69e"
WARNING = "#f2c66d"
ERROR = "#ff7b86"
DISABLED = "#697386"

FONT_PREFERENCES = ("Segoe UI Variable", "Segoe UI", "Arial")
MESSAGE_FONT_MIN = 9
MESSAGE_FONT_DEFAULT = 11
MESSAGE_FONT_MAX = 17


def resolve_font_family(available_families: list[str] | None = None) -> str:
    """Return the first installed Lina font preference or Qt's default family."""
    families = available_families or QFontDatabase.families()
    available = {family.casefold(): family for family in families}
    for preferred in FONT_PREFERENCES:
        if preferred.casefold() in available:
            return available[preferred.casefold()]
    return "Sans Serif"


def clamp_message_font_size(size: int) -> int:
    """Keep session font controls within readable bounds."""
    return max(MESSAGE_FONT_MIN, min(int(size), MESSAGE_FONT_MAX))


def build_stylesheet(font_family: str) -> str:
    """Build Lina's centralized high-contrast Qt stylesheet."""
    return f"""
        QWidget {{
            color: {TEXT_PRIMARY};
            font-family: \"{font_family}\";
            font-size: 11pt;
        }}
        QMainWindow, QWidget#centralWidget, QWidget#chatPanel {{
            background: {APP_BG};
        }}
        QWidget#sidebar {{
            background: {SIDEBAR_BG};
            border-right: 1px solid {BORDER};
        }}
        QWidget#header, QWidget#composerPanel, QWidget#statusPanel {{
            background: {PANEL_BG};
            border: 1px solid {BORDER};
            border-radius: 8px;
        }}
        QLabel#mutedLabel {{ color: {TEXT_MUTED}; }}
        QLabel#statusChip {{
            background: {PANEL_BG};
            color: {TEXT_SECONDARY};
            border: 1px solid {BORDER};
            border-radius: 8px;
            padding: 5px 10px;
        }}
        QLabel#assistantBubble {{
            background: {ASSISTANT_BUBBLE};
            border: 1px solid {BORDER};
            border-radius: 8px;
            padding: 12px;
        }}
        QLabel#userBubble {{
            background: {USER_BUBBLE};
            border-radius: 8px;
            padding: 12px;
        }}
        QPlainTextEdit {{
            background: {COMPOSER_BG};
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER};
            border-radius: 8px;
            padding: 9px;
            selection-background-color: {ACCENT};
        }}
        QPlainTextEdit:focus {{ border: 1px solid {ACCENT}; }}
        QPushButton {{
            background: {PANEL_BG};
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER};
            border-radius: 7px;
            min-height: 34px;
            padding: 4px 11px;
        }}
        QPushButton:hover {{ background: #252b36; border-color: {ACCENT}; }}
        QPushButton:pressed {{ background: #313946; }}
        QPushButton:disabled {{ color: {DISABLED}; border-color: #282e38; }}
        QPushButton#accentButton {{
            background: {ACCENT};
            color: {TEXT_PRIMARY};
            border-color: {ACCENT};
            font-weight: 600;
        }}
        QPushButton#accentButton:hover {{ background: {ACCENT_HOVER}; }}
        QPushButton#copyButton {{
            background: transparent;
            color: {TEXT_SECONDARY};
            border: none;
            min-height: 24px;
            padding: 2px 4px;
        }}
        QScrollArea {{ border: none; background: {APP_BG}; }}
        QScrollBar:vertical {{
            background: {APP_BG};
            width: 10px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {BORDER};
            border-radius: 5px;
            min-height: 32px;
        }}
        QToolTip {{
            background: {PANEL_BG};
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER};
            padding: 5px;
        }}
    """
