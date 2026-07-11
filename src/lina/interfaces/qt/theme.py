"""Theme and font helpers for Lina's PySide6 interface."""

from __future__ import annotations

from PySide6.QtGui import QFontDatabase


APP_BG = "#0e1117"
SIDEBAR_BG = "#0b0e14"
PANEL_BG = "#171b23"
ELEVATED_BG = "#1c222d"
COMPOSER_BG = "#151a22"
ASSISTANT_BUBBLE = "#202631"
USER_BUBBLE = "#2f5fd7"
TEXT_PRIMARY = "#f4f7fb"
TEXT_SECONDARY = "#d7dde7"
TEXT_MUTED = "#9faabc"
ACCENT = "#6f8fff"
ACCENT_HOVER = "#7f9cff"
BORDER = "#2b3340"
SOFT_BORDER = "#394252"
SUCCESS = "#69d79b"
WARNING = "#f0c76e"
ERROR = "#ff7d88"
DISABLED = "#7b8493"

SPACE_XS = 4
SPACE_SM = 8
SPACE_MD = 12
SPACE_LG = 16
SPACE_XL = 24
SPACE_XXL = 32

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
        QWidget#header {{
            background: {PANEL_BG};
            border: 1px solid {BORDER};
            border-radius: 10px;
        }}
        QWidget#composerPanel {{
            background: {PANEL_BG};
            border: 1px solid {BORDER};
            border-radius: 12px;
        }}
        QWidget#screenContextChip {{
            background: {ELEVATED_BG};
            border: 1px solid {ACCENT};
            border-radius: 8px;
        }}
        QWidget#statusPanel {{
            background: transparent;
            border: none;
        }}
        QWidget#assistantBubble {{
            background: {ASSISTANT_BUBBLE};
            border: 1px solid {BORDER};
            border-radius: 14px;
        }}
        QWidget#userBubble {{
            background: {USER_BUBBLE};
            border: 1px solid #3b6bed;
            border-radius: 14px;
        }}
        QLabel#bubbleText {{
            background: transparent;
            border: none;
            padding: 0;
        }}
        QLabel#mutedLabel {{ color: {TEXT_MUTED}; }}
        QLabel#senderLabel {{
            color: {TEXT_MUTED};
            font-weight: 600;
            font-size: 9pt;
        }}
        QLabel#statusChip {{
            background: {ELEVATED_BG};
            color: {TEXT_SECONDARY};
            border: 1px solid {BORDER};
            border-radius: 13px;
            padding: 4px 9px;
            max-height: 28px;
        }}
        QPlainTextEdit {{
            background: {COMPOSER_BG};
            color: {TEXT_PRIMARY};
            border: 1px solid {SOFT_BORDER};
            border-radius: 10px;
            padding: 8px 10px;
            selection-background-color: {ACCENT};
        }}
        QPlainTextEdit:focus {{ border: 1px solid {ACCENT}; }}
        QPushButton {{
            background: {ELEVATED_BG};
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER};
            border-radius: 9px;
            min-height: 32px;
            padding: 4px 10px;
        }}
        QPushButton:hover {{ background: #252c38; border-color: {ACCENT}; }}
        QPushButton:pressed {{ background: #303846; }}
        QPushButton:disabled {{ color: {DISABLED}; border-color: #252b35; }}
        QPushButton#accentButton {{
            background: {ACCENT};
            color: {TEXT_PRIMARY};
            border-color: {ACCENT};
            font-weight: 600;
        }}
        QPushButton#accentButton:hover {{ background: {ACCENT_HOVER}; }}
        QPushButton#composerActionButton {{
            min-height: 46px;
            max-height: 46px;
            padding: 0 13px;
        }}
        QPushButton#copyButton {{
            background: transparent;
            color: {TEXT_MUTED};
            border: none;
            min-height: 20px;
            padding: 0 2px;
            font-size: 9pt;
        }}
        QPushButton#copyButton:hover {{ color: {TEXT_PRIMARY}; }}
        QPushButton#secondaryButton {{
            background: transparent;
            color: {TEXT_SECONDARY};
            min-height: 28px;
            padding: 2px 9px;
        }}
        QPushButton#screenContextRemoveButton {{
            background: transparent;
            color: {TEXT_SECONDARY};
            border: none;
            min-height: 22px;
            padding: 0 4px;
            font-size: 9pt;
        }}
        QPushButton#screenContextRemoveButton:hover {{ color: {TEXT_PRIMARY}; }}
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
