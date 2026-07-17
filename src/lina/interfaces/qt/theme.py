"""Theme and font helpers for Lina's PySide6 interface."""

from __future__ import annotations

from PySide6.QtGui import QFontDatabase
from lina.ui.design import resolve_palette


APP_BG = "#0b111a"
SIDEBAR_BG = "#0d151f"
PANEL_BG = "#111925"
ELEVATED_BG = "#172231"
COMPOSER_BG = "#111925"
ASSISTANT_BUBBLE = "#111925"
USER_BUBBLE = "#1d3d66"
TEXT_PRIMARY = "#edf3fb"
TEXT_SECONDARY = "#c7d1df"
TEXT_MUTED = "#8795a8"
ACCENT = "#4f9cff"
ACCENT_HOVER = "#63adff"
BORDER = "#1d2a3a"
SOFT_BORDER = "#2a3a4f"
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
        QStackedWidget#settingsPages {{ background: transparent; border: none; }}
        QListWidget#settingsNavigation {{ background: transparent; border: none; }}
        QListWidget#settingsNavigation::item {{ margin: 2px 0; padding: 10px 12px; border-radius: 9px; }}
        QListWidget#settingsNavigation::item:selected {{ background: {selected}; color: {text_primary}; border-left: 2px solid {accent}; }}
        QLineEdit#settingsSearch {{ min-height: 40px; border-radius: 10px; padding: 0 12px; }}
        QLabel#settingsDialogTitle {{ font-size: 20pt; font-weight: 650; color: {text_primary}; }}
        QLabel#settingsPageTitle {{ font-size: 18pt; font-weight: 650; color: {text_primary}; }}
        QLabel#settingsDescription {{ color: {text_muted}; padding: 5px 0; }}
        QLabel#settingsSectionTitle {{ font-size: 11pt; font-weight: 650; color: {text_primary}; padding: 0; }}
        QFrame#settingsSectionCard {{ background: {panel_bg}; border: 1px solid {border}; border-radius: 14px; }}
        QFrame#settingsSectionCard QLabel, QFrame#settingsSectionCard QCheckBox {{ background: transparent; }}
        QScrollArea#settingsPageScroll, QScrollArea#settingsPageScroll > QWidget > QWidget {{
            background: {panel_bg}; border: none;
        }}
        QProgressBar#agentProgress {{
            background: {elevated_bg}; border: none; border-radius: 3px; min-height: 6px; max-height: 6px;
        }}
        QProgressBar#agentProgress::chunk {{ background: {accent}; border-radius: 3px; }}
        QWidget#agentPanel {{ background: {panel_bg}; border: 1px solid {border}; border-radius: 14px; }}
        QWidget#agentPanel QLabel {{ background: transparent; border: none; }}
        QComboBox#notificationFilter {{ background: {panel_bg}; font-weight: 600; }}
        QListWidget#notificationItems {{ background: {panel_bg}; }}
        QPushButton#notificationButton {{ min-width: 42px; border-color: {accent}; }}
        QWidget#sidebar {{
            background: {sidebar_bg};
            border-right: 1px solid {soft_border};
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
            background: {app_bg};
            border: none;
            border-bottom: 1px solid {border};
        }}
        QLabel#conversationTitle, QLabel#inspectorTitle, QLabel#sidebarTitle {{
            color: {text_primary}; font-size: 14pt; font-weight: 650;
        }}
        QLabel#conversationSubtitle {{ color: {text_muted}; font-size: 9pt; }}
        QWidget#detailsInspector {{
            background: {sidebar_bg}; border-left: 1px solid {soft_border};
        }}
        QDialog#commandPalette {{ background: {panel_bg}; }}
        QPushButton#unifiedStatusButton {{
            background: transparent; color: {text_muted}; border: 1px solid transparent;
            border-radius: 8px; min-height: 30px; padding: 0 7px;
        }}
        QPushButton#unifiedStatusButton:hover {{ background: {elevated_bg}; color: {text_primary}; }}
        QPushButton#modeChip {{
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
            border: 1px solid {soft_border};
            border-radius: 18px;
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
            border-radius: 10px;
            text-align: left;
            padding: 8px 12px;
            font-size: 10pt;
        }}
        QPushButton#sessionButton:hover {{
            background: {elevated_bg};
            border-color: transparent;
        }}
        QPushButton#sessionButton:checked {{
            background: {selected};
            color: {text_primary};
            border-color: {soft_border};
            font-weight: 600;
        }}
        QLineEdit#conversationSearchInput {{
            background: {composer_bg};
            color: {text_primary};
            border: 1px solid {border};
            border-radius: 10px;
            min-height: 40px;
            padding: 0 12px;
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
            background: {assistant_bubble};
            border: 1px solid {border};
            border-radius: 16px;
        }}
        QWidget#userBubble {{
            background: {user_bubble};
            border: 1px solid {user_border};
            border-radius: 16px;
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
            font-size: 19pt;
            font-weight: 650;
        }}
        QLabel#welcomeSubtitle {{
            color: {text_muted};
            font-size: 11pt;
        }}
        QPushButton#suggestionButton {{
            background: {panel_bg}; color: {text_secondary}; border: 1px solid {soft_border};
            border-radius: 12px; min-height: 44px; padding: 0 14px;
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
        QWidget#composerPanel QPlainTextEdit {{
            background: transparent;
            border: none;
            border-radius: 0;
            padding: 4px 2px;
        }}
        QWidget#composerPanel QPlainTextEdit:focus {{ border: none; }}
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
        QPushButton#primaryNavigationButton {{
            background: {selected}; color: {text_primary}; border: 1px solid {soft_border};
            border-radius: 10px; min-height: 40px; font-weight: 600;
        }}
        QPushButton#primaryNavigationButton:hover {{ background: {elevated_bg}; border-color: {accent}; }}
        QPushButton#composerActionButton {{
            min-height: 38px;
            max-height: 38px;
            padding: 0 13px;
        }}
        QPushButton#composerUtilityButton {{
            background: transparent; color: {text_secondary}; border: 1px solid transparent;
            border-radius: 9px; min-height: 36px; padding: 0 9px;
        }}
        QPushButton#composerUtilityButton:hover {{ background: {elevated_bg}; border-color: {border}; }}
        QPushButton#composerSendButton {{
            background: {accent}; color: {user_text}; border: 1px solid {accent};
            border-radius: 19px; min-width: 38px; max-width: 38px;
            min-height: 38px; max-height: 38px; padding: 0;
        }}
        QPushButton#composerSendButton:hover {{ background: {accent_hover}; border-color: {accent_hover}; }}
        QPushButton#composerSendButton:disabled {{ background: {elevated_bg}; border-color: {border}; color: {disabled}; }}
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
        QMenu {{ background: {panel_bg}; color: {text_primary}; border: 1px solid {soft_border}; padding: 7px; }}
        QMenu::item {{ padding: 8px 24px 8px 11px; border-radius: 7px; }}
        QMenu::item:selected {{ background: {selected}; color: {text_primary}; }}
        QMenu::item:disabled {{ color: {disabled}; }}
        QFrame#toolActivityCard {{ background: {panel_bg}; border: 1px solid {border}; border-radius: 14px; }}
        QFrame#toolActivityCard QLabel {{ background: transparent; border: none; }}
        QLabel#toolActivityTitle {{ color: {text_primary}; font-weight: 650; font-size: 11pt; }}
        QLabel#toolActivityRisk, QLabel#toolActivityDetails {{ color: {text_muted}; }}
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
