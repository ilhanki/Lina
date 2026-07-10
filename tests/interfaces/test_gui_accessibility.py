"""Tests for Lina GUI accessibility and session controls."""

from types import SimpleNamespace

from lina.interfaces.gui import (
    INPUT_PLACEHOLDER,
    SIDEBAR_COLLAPSED_WIDTH,
    SIDEBAR_WIDTH,
    LinaGui,
    calculate_message_wraplength,
    derive_session_title,
)


class FakeWidget:
    def __init__(self) -> None:
        self.config = {}
        self.pack_calls = []
        self.pack_forget_count = 0

    def configure(self, **kwargs) -> None:
        self.config.update(kwargs)

    def pack(self, **kwargs) -> None:
        self.pack_calls.append(kwargs)

    def pack_forget(self) -> None:
        self.pack_forget_count += 1


class FakeFont:
    def __init__(self) -> None:
        self.config = {}

    def configure(self, **kwargs) -> None:
        self.config.update(kwargs)


class FakeText:
    def __init__(self, text: str = "") -> None:
        self.text = text
        self.config = {}

    def get(self, start: str, end: str) -> str:
        return self.text

    def delete(self, start: str, end: str) -> None:
        self.text = ""

    def insert(self, index: str, text: str) -> None:
        self.text = text

    def configure(self, **kwargs) -> None:
        self.config.update(kwargs)


class FakeClipboardRoot:
    def __init__(self) -> None:
        self.text = ""

    def clipboard_clear(self) -> None:
        self.text = ""

    def clipboard_append(self, text: str) -> None:
        self.text = text


def test_session_title_skips_simple_greeting() -> None:
    assert derive_session_title("selam naber") == "Yeni Sohbet"


def test_session_title_is_bounded_and_deterministic() -> None:
    message = "Lina projesi için erişilebilir bir arayüz tasarla"
    title = derive_session_title(message)

    assert title == derive_session_title(message)
    assert title.endswith("...")
    assert len(title) <= 40


def test_message_wraplength_stays_within_readable_bounds() -> None:
    assert calculate_message_wraplength(300) == 280
    assert calculate_message_wraplength(1000) == 700
    assert calculate_message_wraplength(2000) == 760


def test_sidebar_collapses_and_expands() -> None:
    gui = LinaGui.__new__(LinaGui)
    gui._sidebar_expanded = True
    gui._sidebar = FakeWidget()
    gui._sidebar_details = FakeWidget()
    gui._sidebar_footer = FakeWidget()
    gui._new_chat_button = FakeWidget()
    gui._sidebar_toggle_button = FakeWidget()

    gui._toggle_sidebar()

    assert gui._sidebar.config["width"] == SIDEBAR_COLLAPSED_WIDTH
    assert gui._sidebar_details.pack_forget_count == 1
    assert gui._sidebar_footer.pack_forget_count == 1
    assert gui._new_chat_button.config["text"] == "+"

    gui._toggle_sidebar()

    assert gui._sidebar.config["width"] == SIDEBAR_WIDTH
    assert gui._sidebar_details.pack_calls
    assert gui._sidebar_footer.pack_calls
    assert gui._new_chat_button.config["text"] == "Yeni Sohbet"


def test_font_size_controls_respect_bounds() -> None:
    gui = LinaGui.__new__(LinaGui)
    gui._message_font_size = 16
    gui._chat_font = FakeFont()
    statuses = []
    gui._update_status_text = statuses.append

    gui._adjust_font_size(5)
    assert gui._message_font_size == 16

    gui._message_font_size = 9
    gui._adjust_font_size(-5)
    assert gui._message_font_size == 9
    assert statuses[-1] == "Yazı boyutu: 9"


def test_placeholder_is_not_returned_as_user_input() -> None:
    gui = LinaGui.__new__(LinaGui)
    gui._message_input = FakeText(INPUT_PLACEHOLDER)
    gui._input_has_placeholder = True

    assert gui._get_input_text() == ""


def test_placeholder_hides_and_restores_for_empty_input() -> None:
    gui = LinaGui.__new__(LinaGui)
    gui._message_input = FakeText()
    gui._input_has_placeholder = False
    gui._is_waiting_for_response = False
    gui._send_button = FakeWidget()

    gui._show_input_placeholder()
    assert gui._message_input.text == INPUT_PLACEHOLDER
    assert gui._input_has_placeholder is True

    gui._hide_input_placeholder()
    assert gui._message_input.text == ""
    assert gui._input_has_placeholder is False


def test_enter_sends_but_shift_enter_keeps_newline_behavior() -> None:
    gui = LinaGui.__new__(LinaGui)
    send_calls = []
    gui.send_message = lambda: send_calls.append(True)

    assert gui._handle_enter(SimpleNamespace(state=0)) == "break"
    assert gui._handle_enter(SimpleNamespace(state=1)) is None
    assert send_calls == [True]


def test_copy_message_copies_only_selected_message() -> None:
    gui = LinaGui.__new__(LinaGui)
    gui._root = FakeClipboardRoot()
    statuses = []
    gui._update_status_text = statuses.append

    gui._copy_message("Seçili mesaj")

    assert gui._root.text == "Seçili mesaj"
    assert statuses == ["Mesaj kopyalandı"]


def test_input_shortcuts_focus_and_start_new_chat() -> None:
    gui = LinaGui.__new__(LinaGui)
    actions = []
    gui._hide_input_placeholder = lambda: actions.append("hide")
    gui._focus_input = lambda: actions.append("focus")
    gui._handle_new_chat = lambda: actions.append("new")

    assert gui._handle_focus_shortcut() == "break"
    assert gui._handle_new_chat_shortcut() == "break"
    assert actions == ["hide", "focus", "new"]
