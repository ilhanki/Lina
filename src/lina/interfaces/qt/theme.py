"""Theme and font helpers for Lina's PySide6 interface."""

from __future__ import annotations

from PySide6.QtGui import QFontDatabase, QGuiApplication


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


def build_stylesheet(font_family: str, theme: str = "dark", font_scale: float = 1.0) -> str:
    """Build Lina's centralized high-contrast Qt stylesheet."""
    palette = _palette_for_theme(theme)
    app_bg = palette["app_bg"]
    sidebar_bg = palette["sidebar_bg"]
    panel_bg = palette["panel_bg"]
    elevated_bg = palette["elevated_bg"]
    composer_bg = palette["composer_bg"]
    assistant_bubble = palette["assistant_bubble"]
    user_bubble = palette["user_bubble"]
    text_primary = palette["text_primary"]
    text_secondary = palette["text_secondary"]
    text_muted = palette["text_muted"]
    border = palette["border"]
    soft_border = palette["soft_border"]
    accent = palette["accent"]
    accent_hover = palette["accent_hover"]
    disabled = palette["disabled"]
    base_font_size = max(9, min(round(11 * font_scale), 15))
    return f"""
        QWidget {{
            color: {text_primary};
            font-family: \"{font_family}\";
            font-size: {base_font_size}pt;
        }}
        QMainWindow, QWidget#centralWidget, QWidget#chatPanel {{
            background: {app_bg};
        }}
        QWidget#sidebar {{
            background: {sidebar_bg};
            border-right: 1px solid {border};
        }}
        QWidget#header {{
            background: {panel_bg};
            border: 1px solid {border};
            border-radius: 10px;
        }}
        QWidget#composerPanel {{
            background: {panel_bg};
            border: 1px solid {border};
            border-radius: 12px;
        }}
        QWidget#screenContextChip {{
            background: {elevated_bg};
            border: 1px solid {accent};
            border-radius: 8px;
        }}
        QWidget#statusPanel {{
            background: transparent;
            border: none;
        }}
        QPushButton#sessionButton {{
            background: transparent;
            color: {text_secondary};
            border: 1px solid transparent;
            border-radius: 9px;
            text-align: left;
            padding: 7px 12px;
            font-size: 10pt;
        }}
        QPushButton#sessionButton:hover {{
            background: {elevated_bg};
            border-color: {border};
        }}
        QPushButton#sessionButton:checked {{
            background: {elevated_bg};
            color: {text_primary};
            border-color: {accent};
            font-weight: 600;
        }}
        QLineEdit#conversationSearchInput {{
            background: {composer_bg};
            color: {text_primary};
            border: 1px solid {border};
            border-radius: 8px;
            min-height: 36px;
            padding: 0 10px;
        }}
        QLineEdit#conversationSearchInput:focus {{ border-color: {accent}; }}
        QComboBox#conversationFilter {{
            background: {elevated_bg};
            color: {text_secondary};
            border: 1px solid {border};
            border-radius: 7px;
            min-height: 32px;
            padding: 0 8px;
        }}
        QLabel#conversationGroupHeading {{
            color: {text_muted};
            font-size: 9pt;
            padding: 8px 4px 2px;
        }}
        QLabel#conversationEmptyState {{
            color: {text_muted};
            padding: 12px 4px;
        }}
        QPushButton#conversationSearchResult {{
            background: transparent;
            color: {TEXT_SECONDARY};
            border: 1px solid transparent;
            border-radius: 8px;
            text-align: left;
            padding: 7px 10px;
        }}
        QPushButton#conversationSearchResult:hover {{
            background: {ELEVATED_BG};
            border-color: {BORDER};
        }}
        QWidget#assistantBubble {{
            background: {assistant_bubble};
            border: 1px solid {border};
            border-radius: 14px;
        }}
        QWidget#userBubble {{
            background: {user_bubble};
            border: 1px solid #3b6bed;
            border-radius: 14px;
        }}
        QLabel#bubbleText {{
            background: transparent;
            border: none;
            padding: 0;
        }}
        QLabel#messageImagePreview {{
            background: {composer_bg};
            border: 1px solid {soft_border};
            border-radius: 8px;
            padding: 2px;
        }}
        QLabel#mutedLabel {{ color: {text_muted}; }}
        QLabel#sessionDateLabel {{
            color: {text_muted};
            font-size: 9pt;
        }}
        QWidget#welcomeState {{ background: transparent; }}
        QLabel#welcomeGreeting {{
            color: {text_primary};
            font-size: 20pt;
            font-weight: 700;
        }}
        QLabel#welcomeSubtitle {{
            color: {text_muted};
            font-size: 11pt;
        }}
        QLabel#welcomeFallbackLogo {{
            color: {ACCENT};
            font-size: 42pt;
            font-weight: 700;
        }}
        QLabel#senderLabel {{
            color: {TEXT_MUTED};
            font-weight: 600;
            font-size: 9pt;
        }}
        QLabel#statusChip {{
            background: {elevated_bg};
            color: {text_secondary};
            border: 1px solid {border};
            border-radius: 13px;
            padding: 4px 9px;
            max-height: 28px;
        }}
        QPlainTextEdit {{
            background: {composer_bg};
            color: {text_primary};
            border: 1px solid {soft_border};
            border-radius: 10px;
            padding: 8px 10px;
            selection-background-color: {ACCENT};
        }}
        QPlainTextEdit:focus {{ border: 1px solid {accent}; }}
        QPushButton {{
            background: {elevated_bg};
            color: {text_primary};
            border: 1px solid {border};
            border-radius: 9px;
            min-height: 32px;
            padding: 4px 10px;
        }}
        QPushButton:hover {{ background: {elevated_bg}; border-color: {accent}; }}
        QPushButton:pressed {{ background: #303846; }}
        QPushButton:disabled {{ color: {disabled}; border-color: {soft_border}; }}
        QPushButton#accentButton {{
            background: {accent};
            color: {text_primary};
            border-color: {accent};
            font-weight: 600;
        }}
        QPushButton#accentButton:hover {{ background: {accent_hover}; }}
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
        QScrollArea {{ border: none; background: {app_bg}; }}
        QScrollBar:vertical {{
            background: {app_bg};
            width: 10px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {border};
            border-radius: 5px;
            min-height: 32px;
        }}
        QToolTip {{
            background: {panel_bg};
            color: {text_primary};
            border: 1px solid {border};
            padding: 5px;
        }}
    """


def _palette_for_theme(theme: str) -> dict[str, str]:
    if theme == "system":
        application = QGuiApplication.instance()
        if application is not None:
            theme = "light" if application.palette().window().color().lightness() > 160 else "dark"
    if theme == "light":
        return {
            "app_bg": "#f4f6f8", "sidebar_bg": "#e9edf2", "panel_bg": "#ffffff",
            "elevated_bg": "#eef1f5", "composer_bg": "#ffffff", "assistant_bubble": "#ffffff",
            "user_bubble": "#3767d6", "text_primary": "#17202b", "text_secondary": "#304052",
            "text_muted": "#5d6b7b", "border": "#c7d0da", "soft_border": "#b5c0cc",
            "accent": "#315fd4", "accent_hover": "#2552c4", "disabled": "#8995a3",
        }
    return {
        "app_bg": APP_BG, "sidebar_bg": SIDEBAR_BG, "panel_bg": PANEL_BG,
        "elevated_bg": ELEVATED_BG, "composer_bg": COMPOSER_BG,
        "assistant_bubble": ASSISTANT_BUBBLE, "user_bubble": USER_BUBBLE,
        "text_primary": TEXT_PRIMARY, "text_secondary": TEXT_SECONDARY,
        "text_muted": TEXT_MUTED, "border": BORDER, "soft_border": SOFT_BORDER,
        "accent": ACCENT, "accent_hover": ACCENT_HOVER, "disabled": DISABLED,
    }
