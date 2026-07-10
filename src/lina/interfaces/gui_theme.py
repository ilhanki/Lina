"""Theme, DPI, and font helpers for Lina's Tkinter interface."""

from __future__ import annotations

import sys
from typing import Any, Iterable


COLOR_APP_BG = "#0f1117"
COLOR_SIDEBAR_BG = "#0a0c11"
COLOR_CHAT_BG = "#0f1117"
COLOR_PANEL_BG = "#181c24"
COLOR_INPUT_BG = "#1d222c"
COLOR_ASSISTANT_BUBBLE = "#222833"
COLOR_USER_BUBBLE = "#315fe8"
COLOR_TEXT_PRIMARY = "#f5f7fb"
COLOR_TEXT_SECONDARY = "#d4dae4"
COLOR_TEXT_MUTED = "#aab4c3"
COLOR_ACCENT = "#5f86ff"
COLOR_ACCENT_HOVER = "#7396ff"
COLOR_BORDER = "#343c49"
COLOR_BUTTON_BG = "#252b36"
COLOR_BUTTON_HOVER = "#313946"
COLOR_DISABLED = "#697386"
COLOR_ERROR = "#ff7b86"
COLOR_SUCCESS = "#65d69e"
COLOR_WARNING = "#f2c66d"

FONT_FAMILY_PREFERENCES = (
    "Segoe UI Variable",
    "Segoe UI",
    "Arial",
    "TkDefaultFont",
)
FONT_MESSAGE_DEFAULT = 11
FONT_MESSAGE_MIN = 9
FONT_MESSAGE_MAX = 16
FONT_LABEL = 10
FONT_MUTED = 10
FONT_HEADER = 16
FONT_TITLE = 18


def configure_windows_dpi_awareness(
    platform_name: str | None = None,
    windll: Any | None = None,
) -> bool:
    """Enable the best available Windows process DPI awareness mode."""
    if (platform_name or sys.platform) != "win32":
        return False

    if windll is None:
        try:
            import ctypes

            windll = ctypes.windll
        except (AttributeError, ImportError):
            return False

    try:
        windll.shcore.SetProcessDpiAwareness(2)
        return True
    except (AttributeError, OSError):
        pass

    try:
        windll.user32.SetProcessDPIAware()
        return True
    except (AttributeError, OSError):
        return False


def configure_tk_scaling(root: Any) -> float:
    """Set a bounded Tk scaling value derived from the current display DPI."""
    try:
        scaling = root.winfo_fpixels("1i") / 72.0
        scaling = max(1.0, min(scaling, 2.0))
        root.tk.call("tk", "scaling", scaling)
        return scaling
    except (AttributeError, RuntimeError, TypeError):
        return 1.0


def resolve_font_family(available_families: Iterable[str]) -> str:
    """Resolve a readable installed font using Lina's fallback order."""
    available = {family.casefold(): family for family in available_families}
    for preferred in FONT_FAMILY_PREFERENCES[:-1]:
        if preferred.casefold() in available:
            return available[preferred.casefold()]
    return FONT_FAMILY_PREFERENCES[-1]


def clamp_message_font_size(size: int) -> int:
    """Clamp a session font size to Lina's accessibility bounds."""
    return max(FONT_MESSAGE_MIN, min(int(size), FONT_MESSAGE_MAX))
