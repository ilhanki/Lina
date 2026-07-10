"""Tests for GUI DPI, font, and theme helpers."""

from lina.interfaces.gui_theme import (
    COLOR_APP_BG,
    COLOR_TEXT_PRIMARY,
    FONT_MESSAGE_DEFAULT,
    clamp_message_font_size,
    configure_tk_scaling,
    configure_windows_dpi_awareness,
    resolve_font_family,
)


class FakeDpiApi:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.calls = []

    def SetProcessDpiAwareness(self, mode: int) -> None:
        self.calls.append(mode)
        if self.should_fail:
            raise OSError("unsupported")


class FakeLegacyDpiApi:
    def __init__(self) -> None:
        self.call_count = 0

    def SetProcessDPIAware(self) -> None:
        self.call_count += 1


class FakeWindll:
    def __init__(self, modern_should_fail: bool = False) -> None:
        self.shcore = FakeDpiApi(should_fail=modern_should_fail)
        self.user32 = FakeLegacyDpiApi()


class FakeTkInterpreter:
    def __init__(self) -> None:
        self.calls = []

    def call(self, *args) -> None:
        self.calls.append(args)


class FakeRoot:
    def __init__(self, dpi: float) -> None:
        self._dpi = dpi
        self.tk = FakeTkInterpreter()

    def winfo_fpixels(self, value: str) -> float:
        assert value == "1i"
        return self._dpi


def test_windows_dpi_helper_uses_modern_api() -> None:
    windll = FakeWindll()

    assert configure_windows_dpi_awareness("win32", windll) is True
    assert windll.shcore.calls == [2]
    assert windll.user32.call_count == 0


def test_windows_dpi_helper_uses_legacy_fallback() -> None:
    windll = FakeWindll(modern_should_fail=True)

    assert configure_windows_dpi_awareness("win32", windll) is True
    assert windll.user32.call_count == 1


def test_dpi_helper_is_safe_on_unsupported_platform() -> None:
    windll = FakeWindll()

    assert configure_windows_dpi_awareness("linux", windll) is False
    assert windll.shcore.calls == []


def test_tk_scaling_uses_display_dpi_and_bounds_value() -> None:
    root = FakeRoot(dpi=144.0)

    scaling = configure_tk_scaling(root)

    assert scaling == 2.0
    assert root.tk.calls == [("tk", "scaling", 2.0)]


def test_font_family_prefers_segoe_ui_variable() -> None:
    assert resolve_font_family(["Arial", "Segoe UI", "Segoe UI Variable"]) == (
        "Segoe UI Variable"
    )


def test_font_family_uses_safe_fallback() -> None:
    assert resolve_font_family(["Consolas"]) == "TkDefaultFont"


def test_message_font_size_is_bounded() -> None:
    assert clamp_message_font_size(4) == 9
    assert clamp_message_font_size(FONT_MESSAGE_DEFAULT) == FONT_MESSAGE_DEFAULT
    assert clamp_message_font_size(40) == 16


def test_theme_has_high_contrast_primary_colors() -> None:
    assert COLOR_APP_BG != COLOR_TEXT_PRIMARY
