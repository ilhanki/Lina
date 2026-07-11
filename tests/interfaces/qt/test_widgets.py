"""Tests for PySide6 GUI widgets."""

from PySide6.QtCore import Qt

from lina.interfaces.qt.theme import clamp_message_font_size, resolve_font_family
from lina.interfaces.qt.widgets import ChatMessageWidget, ComposerWidget, SidebarWidget


def test_theme_clamps_message_font_size() -> None:
    assert clamp_message_font_size(1) == 9
    assert clamp_message_font_size(12) == 12
    assert clamp_message_font_size(99) == 17


def test_resolve_font_family_prefers_available_family() -> None:
    assert resolve_font_family(["Arial", "Other"]) == "Arial"


def test_chat_message_is_selectable_and_copyable(qtbot) -> None:
    widget = ChatMessageWidget("assistant", "Merhaba", "Arial", 11)
    qtbot.addWidget(widget)

    with qtbot.waitSignal(widget.copy_requested, timeout=1000) as signal:
        widget.copy_button.click()

    assert signal.args == ["Merhaba"]
    assert widget.text_label.textInteractionFlags() & Qt.TextInteractionFlag.TextSelectableByMouse


def test_composer_sends_with_enter_and_keeps_shift_enter_newline(qtbot) -> None:
    composer = ComposerWidget("Arial", 11)
    qtbot.addWidget(composer)
    composer.set_text("Merhaba")

    with qtbot.waitSignal(composer.send_requested, timeout=1000):
        qtbot.keyClick(composer.input, Qt.Key.Key_Return)

    qtbot.keyClick(composer.input, Qt.Key.Key_Return, modifier=Qt.KeyboardModifier.ShiftModifier)
    assert "\n" in composer.input.toPlainText()


def test_composer_appends_transcription_to_existing_draft(qtbot) -> None:
    composer = ComposerWidget("Arial", 11)
    qtbot.addWidget(composer)

    composer.set_text("yarın şunu yap")

    assert composer.append_transcription("roadmap dosyasını aç") is True
    assert composer.text() == "yarın şunu yap roadmap dosyasını aç"


def test_sidebar_collapses_without_destroying_branding(qtbot, tmp_path) -> None:
    sidebar = SidebarWidget(tmp_path / "missing.png", "v0.test", "llama3")
    qtbot.addWidget(sidebar)

    sidebar.toggle()

    assert sidebar.is_expanded is False
    assert sidebar.width() == SidebarWidget.COLLAPSED_WIDTH
    assert sidebar.logo_label.text() == "L"
