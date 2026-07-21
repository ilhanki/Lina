from lina.interfaces.qt.theme import build_stylesheet, theme_palette
from pathlib import Path
import re


def _contrast(first: str, second: str) -> float:
    def luminance(value: str) -> float:
        channels = [int(value[index:index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]
    high, low = sorted((luminance(first), luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def test_light_palette_semantic_tokens_have_readable_contrast() -> None:
    palette = theme_palette("light")
    required = {"app_bg", "panel_bg", "text_primary", "text_secondary", "text_muted", "accent", "focus", "disabled", "success", "warning", "error", "info", "user_text"}
    assert required <= palette.keys()
    assert _contrast(palette["text_primary"], palette["panel_bg"]) >= 7
    assert _contrast(palette["text_muted"], palette["panel_bg"]) >= 4.5
    assert _contrast(palette["user_text"], palette["user_bubble"]) >= 4.5
    assert palette["selected"] != palette["elevated_bg"]
    assert palette["focus"] != palette["border"]


def test_dark_palette_regression_and_system_resolution() -> None:
    dark = theme_palette("dark")
    assert theme_palette("system", system_lightness=40) == dark
    assert theme_palette("system", system_lightness=220) == theme_palette("light")
    assert dark["app_bg"] == "#070d18"
    assert dark["user_bubble"] == "#173b77"
    assert dark["assistant_bubble"] != dark["app_bg"]


def test_stylesheet_uses_theme_specific_component_states() -> None:
    light = build_stylesheet("Segoe UI", "light", 1.0)
    dark = build_stylesheet("Segoe UI", "dark", 1.0)
    palette = theme_palette("light")
    for selector in ("QFrame#toolActivityCard", "QListWidget::item:selected", "QPushButton:disabled", "QPushButton:focus", "QMenu::item:selected", "QCheckBox::indicator:checked", "QSlider::handle:horizontal", "QToolTip"):
        assert selector in light
    assert palette["text_primary"] in light
    assert palette["selected"] in light
    assert palette["focus"] in light
    assert light != dark
    assert "#303846" not in light
    assert "QScrollArea#chatTimelineScroll" in light
    assert "QScrollArea#sidebarConversationScroll" in light
    assert "QWidget#chatTimelineViewport" in light
    assert "QWidget#sidebarConversationViewport" in light
    assert "QWidget#detailsInspector" in light
    assert "QPushButton#unifiedStatusButton" in light
    assert 'QLabel#readyStatusDot[state="active"]' in light
    assert 'QLabel#readyStatusDot[state="warning"]' in light
    assert 'QLabel#readyStatusDot[state="error"]' in light
    assert "QPushButton#primaryNavigationButton" in light
    assert "QPushButton#composerSendButton" in light
    assert 'QWidget#composerPanel[active="true"]' in light
    assert "QPushButton#contextToolCard" in light
    assert "QFrame#sessionAccent" in light
    assert "QFrame#settingsSectionCard" in light
    assert "QSpinBox, QDoubleSpinBox" in light
    assert "QSpinBox::up-button" in light
    assert "QDoubleSpinBox:disabled" in light
    assert "QTabWidget::pane" in light
    assert "QTabBar::tab:selected" in light
    assert "QProgressBar::chunk" in light


def test_font_scale_bounds_are_reflected_without_component_changes() -> None:
    small = build_stylesheet("Segoe UI", "light", 0.85)
    large = build_stylesheet("Segoe UI", "light", 1.35)
    assert "font-size: 9pt" in small
    assert "font-size: 15pt" in large
    assert "QFrame#toolActivityCard" in small and "QFrame#toolActivityCard" in large
    assert "QListWidget" in small and "QListWidget" in large


def test_widgets_do_not_embed_theme_specific_hex_colors() -> None:
    root = Path(__file__).resolve().parents[3] / "src" / "lina" / "interfaces" / "qt"
    exceptions = {"theme.py", "region_capture_overlay.py"}
    violations = []
    for path in root.rglob("*.py"):
        if path.name in exceptions:
            continue
        if re.search(r"#[0-9a-fA-F]{3,8}\b", path.read_text(encoding="utf-8")):
            violations.append(path.name)
    assert violations == []
