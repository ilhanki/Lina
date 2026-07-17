"""Single source of truth for Lina visual and interaction metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from PySide6.QtGui import QGuiApplication


ThemeName = Literal["dark", "light", "system"]


@dataclass(frozen=True, slots=True)
class ColorPalette:
    canvas: str
    surface_primary: str
    surface_secondary: str
    surface_elevated: str
    surface_hover: str
    surface_pressed: str
    surface_selected: str
    border_subtle: str
    border_default: str
    border_focus: str
    text_primary: str
    text_secondary: str
    text_tertiary: str
    text_disabled: str
    accent: str
    accent_hover: str
    accent_pressed: str
    success: str
    warning: str
    danger: str
    information: str
    overlay: str
    scrim: str
    user_surface: str
    user_text: str

    def as_legacy_dict(self) -> dict[str, str]:
        """Keep established QSS and extensions source-compatible during migration."""
        return {
            "app_bg": self.canvas, "sidebar_bg": self.surface_secondary,
            "panel_bg": self.surface_primary, "elevated_bg": self.surface_elevated,
            "composer_bg": self.surface_primary, "assistant_bubble": self.canvas,
            "user_bubble": self.user_surface, "text_primary": self.text_primary,
            "text_secondary": self.text_secondary, "text_muted": self.text_tertiary,
            "border": self.border_default, "soft_border": self.border_subtle,
            "accent": self.accent, "accent_hover": self.accent_hover,
            "disabled": self.text_disabled, "pressed": self.surface_pressed,
            "selected": self.surface_selected, "focus": self.border_focus,
            "user_border": self.accent_pressed, "user_text": self.user_text,
            "success": self.success, "warning": self.warning,
            "error": self.danger, "info": self.information,
        }


@dataclass(frozen=True, slots=True)
class SpacingTokens:
    xxs: int = 2
    xs: int = 4
    sm: int = 6
    md: int = 8
    lg: int = 12
    xl: int = 16
    xxl: int = 20
    xxxl: int = 24
    huge: int = 32
    giant: int = 40
    jumbo: int = 48
    max: int = 64


@dataclass(frozen=True, slots=True)
class RadiusTokens:
    xs: int = 4
    sm: int = 6
    md: int = 8
    lg: int = 12
    xl: int = 16
    pill: int = 999


@dataclass(frozen=True, slots=True)
class TypographyTokens:
    display: int = 22
    title_large: int = 18
    title: int = 15
    subtitle: int = 12
    body: int = 11
    body_compact: int = 10
    label: int = 10
    caption: int = 9
    monospace_family: str = "Cascadia Mono, Consolas"


@dataclass(frozen=True, slots=True)
class ControlMetrics:
    compact: int = 30
    default: int = 36
    large: int = 42
    composer: int = 46
    icon_small: int = 16
    icon_default: int = 20
    icon_large: int = 24


@dataclass(frozen=True, slots=True)
class LayoutMetrics:
    navigation_expanded: int = 280
    navigation_collapsed: int = 60
    content_maximum: int = 1180
    chat_readable: int = 820
    inspector_width: int = 320
    composer_maximum: int = 860
    message_spacing: int = 20
    header_height: int = 68
    compact_breakpoint: int = 800
    medium_breakpoint: int = 1120


@dataclass(frozen=True, slots=True)
class MotionTokens:
    fast_ms: int = 90
    normal_ms: int = 160
    slow_ms: int = 240


@dataclass(frozen=True, slots=True)
class DesignTokens:
    palette: ColorPalette
    spacing: SpacingTokens = SpacingTokens()
    radius: RadiusTokens = RadiusTokens()
    typography: TypographyTokens = TypographyTokens()
    controls: ControlMetrics = ControlMetrics()
    layout: LayoutMetrics = LayoutMetrics()
    motion: MotionTokens = MotionTokens()


_DARK = ColorPalette(
    canvas="#0b111a", surface_primary="#111925", surface_secondary="#0d151f",
    surface_elevated="#172231", surface_hover="#1b293b", surface_pressed="#223247",
    surface_selected="#192c45", border_subtle="#1d2a3a", border_default="#2a3a4f",
    border_focus="#63adff", text_primary="#edf3fb", text_secondary="#c2ccda",
    text_tertiary="#8492a5", text_disabled="#607084", accent="#4f9cff",
    accent_hover="#68acff", accent_pressed="#347fda", success="#55d990",
    warning="#e7bd68", danger="#f17b86", information="#6caeff",
    overlay="#111925", scrim="#02060db3", user_surface="#1d3d66", user_text="#f7fbff",
)

_LIGHT = ColorPalette(
    canvas="#f4f7fb", surface_primary="#ffffff", surface_secondary="#edf2f7",
    surface_elevated="#e7eef6", surface_hover="#dfe8f2", surface_pressed="#d4dfeb",
    surface_selected="#dcecff", border_subtle="#d9e2ec", border_default="#b9c8d8",
    border_focus="#1671d9", text_primary="#142033", text_secondary="#34475e",
    text_tertiary="#66788d", text_disabled="#8795a6", accent="#1671d9",
    accent_hover="#0e62c2", accent_pressed="#0a4f9e", success="#14713d",
    warning="#7a4b00", danger="#a8202a", information="#2858c7",
    overlay="#ffffff", scrim="#10182055", user_surface="#176bc5", user_text="#ffffff",
)


def resolve_palette(theme: ThemeName | str, system_lightness: int | None = None) -> ColorPalette:
    if theme not in {"dark", "light", "system"}:
        raise ValueError(f"Unsupported theme: {theme}")
    resolved = theme
    if theme == "system":
        if system_lightness is None:
            application = QGuiApplication.instance()
            system_lightness = application.palette().window().color().lightness() if application is not None else 0
        resolved = "light" if system_lightness > 160 else "dark"
    return _LIGHT if resolved == "light" else _DARK


def design_tokens(theme: ThemeName | str, system_lightness: int | None = None) -> DesignTokens:
    return DesignTokens(resolve_palette(theme, system_lightness))


def contrast_ratio(first: str, second: str) -> float:
    def luminance(value: str) -> float:
        if len(value) != 7 or not value.startswith("#"):
            raise ValueError("Contrast colors must use #RRGGBB")
        channels = [int(value[index:index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]
    high, low = sorted((luminance(first), luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)
