import pytest

from lina.ui.design import contrast_ratio, design_tokens, resolve_palette
from lina.ui.design import standard_icon
from PySide6.QtWidgets import QWidget


def test_design_scales_and_layout_metrics_are_centralized():
    tokens = design_tokens("dark")
    assert tuple(vars(tokens.spacing).values()) if hasattr(tokens.spacing, "__dict__") else tokens.spacing.max == 64
    assert tokens.spacing.xxs == 2 and tokens.spacing.max == 64
    assert tokens.radius.pill == 999
    assert tokens.radius.message == 18 and tokens.radius.composer == 20
    assert tokens.spacing.ten == 10 and tokens.spacing.twenty_eight == 28
    assert tokens.elevation.menu > tokens.elevation.floating
    assert tokens.layout.navigation_expanded == 292
    assert tokens.layout.navigation_collapsed == 64
    assert 760 <= tokens.layout.chat_readable <= 920
    assert tokens.layout.inspector_minimum <= tokens.layout.inspector_width <= tokens.layout.inspector_maximum


def test_light_dark_and_system_palettes_have_critical_contrast():
    for theme in ("dark", "light"):
        palette = resolve_palette(theme)
        assert contrast_ratio(palette.text_primary, palette.canvas) >= 7
        assert contrast_ratio(palette.user_text, palette.user_surface) >= 4.5
    assert resolve_palette("system", 220) == resolve_palette("light")
    assert resolve_palette("system", 20) == resolve_palette("dark")


def test_invalid_theme_and_color_are_rejected():
    with pytest.raises(ValueError):
        resolve_palette("neon")
    with pytest.raises(ValueError):
        contrast_ratio("red", "#ffffff")


def test_standard_icons_are_theme_aware_and_unknown_names_fail(qtbot):
    widget = QWidget()
    qtbot.addWidget(widget)
    assert not standard_icon(widget, "settings").isNull()
    assert standard_icon(widget, "memory", 16).cacheKey() == standard_icon(widget, "memory", 16).cacheKey()
    with pytest.raises(ValueError):
        standard_icon(widget, "settings", 17)
    with pytest.raises(ValueError):
        standard_icon(widget, "brand-copy")
