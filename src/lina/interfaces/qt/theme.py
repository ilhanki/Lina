"""Theme and font helpers for Lina's PySide6 interface."""

from __future__ import annotations

from PySide6.QtGui import QFontDatabase
from lina.ui.design import resolve_palette


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
    palette = theme_palette(theme)
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
    pressed = palette["pressed"]
    selected = palette["selected"]
    focus = palette["focus"]
    user_border = palette["user_border"]
    user_text = palette["user_text"]
    success = palette["success"]
    warning = palette["warning"]
    error = palette["error"]
    info = palette["info"]
    base_font_size = max(9, min(round(11 * font_scale), 15))
    return f"""
        QWidget {{
            color: {text_primary};
            font-family: \"{font_family}\";
            font-size: {base_font_size}pt;
        }}
        QMainWindow, QDialog, QMessageBox, QWidget#centralWidget, QWidget#chatPanel {{
            background: {app_bg};
        }}
        QDialog#notificationCenter, QDialog#reminderDialog {{ background: {app_bg}; }}
        QStackedWidget#settingsPages {{ background: {panel_bg}; border: 1px solid {border}; border-radius: 9px; }}
        QListWidget#settingsNavigation {{ background: {sidebar_bg}; border: 1px solid {border}; }}
        QListWidget#settingsNavigation::item {{ margin: 2px; padding: 9px; }}
        QListWidget#settingsNavigation::item:selected {{ background: {selected}; color: {text_primary}; border-left: 3px solid {accent}; }}
        QComboBox#notificationFilter {{ background: {panel_bg}; font-weight: 600; }}
        QListWidget#notificationItems {{ background: {panel_bg}; }}
        QPushButton#notificationButton {{ min-width: 42px; border-color: {accent}; }}
        QWidget#sidebar {{
            background: {sidebar_bg};
            border-right: 1px solid {border};
        }}
        QWidget#sidebarSessionPanel, QWidget#sidebarStatusPanel,
        QWidget#sidebarConversationViewport, QWidget#sidebarConversationList,
        QScrollArea#sidebarConversationScroll {{
            background: {sidebar_bg};
            border: none;
        }}
        QScrollArea#chatTimelineScroll, QWidget#chatTimelineViewport, QWidget#chatTimeline {{
            background: {app_bg};
            border: none;
        }}
        QWidget#header {{
            background: transparent;
            border: none;
            border-bottom: 1px solid {soft_border};
        }}
        QLabel#conversationTitle, QLabel#inspectorTitle, QLabel#sidebarTitle {{
            color: {text_primary}; font-size: 14pt; font-weight: 650;
        }}
        QLabel#conversationSubtitle {{ color: {text_muted}; font-size: 9pt; }}
        QWidget#detailsInspector {{
            background: {panel_bg}; border-left: 1px solid {soft_border};
        }}
        QDialog#commandPalette {{ background: {panel_bg}; }}
        QPushButton#unifiedStatusButton, QPushButton#modeChip {{
            background: {elevated_bg}; color: {text_secondary}; border: 1px solid {soft_border};
            border-radius: 15px; min-height: 30px; padding: 0 10px;
        }}
        QPushButton#iconButton, QPushButton#sidebarCollapseButton {{
            background: transparent; border: 1px solid transparent; min-width: 30px;
            min-height: 30px; padding: 0 7px;
        }}
        QPushButton#iconButton:hover, QPushButton#sidebarCollapseButton:hover {{
            background: {elevated_bg}; border-color: {soft_border};
        }}
        QPushButton#sidebarShortcut {{
            background: transparent; color: {text_secondary}; border: 1px solid transparent;
            text-align: left; min-height: 34px; padding: 0 9px;
        }}
        QPushButton#sidebarShortcut:hover {{ background: {elevated_bg}; border-color: {soft_border}; }}
        QWidget#composerPanel {{
            background: {panel_bg};
            border: 1px solid {border};
            border-radius: 12px;
        }}
        QWidget#composerRow, QWidget#composerToolbar, QWidget#messageActions {{ background: transparent; border: none; }}
        QLabel#composerHint {{ color: {text_muted}; font-size: 9pt; }}
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
            color: {text_secondary};
            border: 1px solid transparent;
            border-radius: 8px;
            text-align: left;
            padding: 7px 10px;
        }}
        QPushButton#conversationSearchResult:hover {{
            background: {elevated_bg};
            border-color: {border};
        }}
        QWidget#assistantBubble {{
            background: transparent;
            border: none;
            border-radius: 0;
        }}
        QWidget#userBubble {{
            background: {user_bubble};
            border: 1px solid {user_border};
            border-radius: 14px;
        }}
        QWidget#userBubble QLabel {{ color: {user_text}; }}
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
        QLabel#mutedLabel, QLabel#messageTimestamp {{ color: {text_muted}; }}
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
        QPushButton#suggestionButton {{
            background: {panel_bg}; color: {text_secondary}; border: 1px solid {soft_border};
            border-radius: 10px; min-height: 38px; padding: 0 12px;
        }}
        QLabel#welcomeFallbackLogo {{
            color: {accent};
            font-size: 42pt;
            font-weight: 700;
        }}
        QLabel#senderLabel {{
            color: {text_muted};
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
            selection-background-color: {selected};
        }}
        QPlainTextEdit:focus, QLineEdit:focus, QComboBox:focus, QListWidget:focus {{ border: 2px solid {focus}; }}
        QPushButton {{
            background: {elevated_bg};
            color: {text_primary};
            border: 1px solid {border};
            border-radius: 9px;
            min-height: 32px;
            padding: 4px 10px;
        }}
        QPushButton:hover {{ background: {selected}; border-color: {accent}; }}
        QPushButton:pressed {{ background: {pressed}; }}
        QPushButton:focus {{ border: 2px solid {focus}; }}
        QPushButton:disabled {{ color: {disabled}; background: {panel_bg}; border-color: {soft_border}; }}
        QPushButton#accentButton {{
            background: {accent};
            color: {user_text};
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
            color: {text_muted};
            border: none;
            min-height: 20px;
            padding: 0 2px;
            font-size: 9pt;
        }}
        QPushButton#copyButton:hover {{ color: {text_primary}; }}
        QPushButton#secondaryButton {{
            background: transparent;
            color: {text_secondary};
            min-height: 28px;
            padding: 2px 9px;
        }}
        QPushButton#screenContextRemoveButton {{
            background: transparent;
            color: {text_secondary};
            border: none;
            min-height: 22px;
            padding: 0 4px;
            font-size: 9pt;
        }}
        QPushButton#screenContextRemoveButton:hover {{ color: {text_primary}; }}
        QLineEdit, QComboBox, QDateTimeEdit, QListWidget {{
            background: {composer_bg};
            color: {text_primary};
            border: 1px solid {border};
            border-radius: 8px;
            padding: 5px 8px;
            selection-background-color: {selected};
        }}
        QLineEdit:disabled, QComboBox:disabled, QDateTimeEdit:disabled, QListWidget:disabled {{
            color: {disabled}; background: {elevated_bg}; border-color: {soft_border};
        }}
        QListWidget::item {{ padding: 7px; border-radius: 6px; }}
        QListWidget::item:hover {{ background: {elevated_bg}; }}
        QListWidget::item:selected {{ background: {selected}; color: {text_primary}; }}
        QComboBox QAbstractItemView {{
            background: {panel_bg}; color: {text_primary}; border: 1px solid {border};
            selection-background-color: {selected}; selection-color: {text_primary};
        }}
        QCheckBox {{ color: {text_primary}; spacing: 8px; }}
        QCheckBox:disabled {{ color: {disabled}; }}
        QCheckBox::indicator {{ width: 17px; height: 17px; border: 1px solid {border}; border-radius: 4px; background: {composer_bg}; }}
        QCheckBox::indicator:checked {{ background: {accent}; border-color: {accent}; }}
        QCheckBox::indicator:focus {{ border: 2px solid {focus}; }}
        QSlider::groove:horizontal {{ height: 5px; background: {border}; border-radius: 2px; }}
        QSlider::sub-page:horizontal {{ background: {accent}; border-radius: 2px; }}
        QSlider::handle:horizontal {{ width: 16px; margin: -6px 0; background: {panel_bg}; border: 2px solid {accent}; border-radius: 8px; }}
        QMenu {{ background: {panel_bg}; color: {text_primary}; border: 1px solid {border}; padding: 5px; }}
        QMenu::item {{ padding: 7px 22px 7px 10px; border-radius: 5px; }}
        QMenu::item:selected {{ background: {selected}; color: {text_primary}; }}
        QMenu::item:disabled {{ color: {disabled}; }}
        QFrame#toolActivityCard {{ background: {panel_bg}; border: 1px solid {border}; border-radius: 10px; }}
        QFrame#toolActivityCard QLabel {{ background: transparent; border: none; }}
        QLabel#toolStatusSuccess {{ color: {success}; font-weight: 600; }}
        QLabel#toolStatusFailure {{ color: {error}; font-weight: 600; }}
        QLabel#toolStatusWarning {{ color: {warning}; font-weight: 600; }}
        QLabel#toolStatusInfo {{ color: {info}; font-weight: 600; }}
        QLabel#errorLabel {{ color: {error}; font-weight: 600; }}
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
        QScrollBar::handle:vertical:hover {{ background: {accent}; }}
        QToolTip {{
            background: {panel_bg};
            color: {text_primary};
            border: 1px solid {border};
            padding: 5px;
        }}
    """


def theme_palette(theme: str, system_lightness: int | None = None) -> dict[str, str]:
    """Return semantic colors for dark, light, or the current system palette."""
    return resolve_palette(theme, system_lightness).as_legacy_dict()


_palette_for_theme = theme_palette
