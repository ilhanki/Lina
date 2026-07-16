"""Tests for PySide6 GUI widgets."""

from datetime import datetime, timezone

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, Qt
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QPushButton

from lina.interfaces.qt.theme import clamp_message_font_size, resolve_font_family
from lina.interfaces.qt.widgets import ChatMessageWidget, ComposerWidget, SidebarWidget
from lina.interfaces.qt.widgets.chat_message import MIN_BUBBLE_WIDTH
from lina.interfaces.qt.widgets.composer import (
    COMPOSER_BUTTON_HEIGHT,
    COMPOSER_INPUT_MAX_HEIGHT,
    COMPOSER_INPUT_MIN_HEIGHT,
)
from lina.interfaces.qt.widgets.welcome_state import WelcomeStateWidget
from lina.screen.models import ScreenContext
from lina.conversations.models import ConversationSession
from lina.conversations.models import ConversationSearchResult


def _visual_context(image_bytes: bytes) -> ScreenContext:
    return ScreenContext(
        image_bytes=image_bytes,
        width=320,
        height=180,
        captured_at=datetime.now(),
        display_name="test.png",
        estimated_byte_size=len(image_bytes),
        source="local_file",
    )


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
    assert widget.sender_label.text() == "Lina"
    assert widget.timestamp_label.text()
    assert widget.copy_button.parent() is widget.action_bar


def test_chat_message_uses_natural_minimum_bubble_width(qtbot) -> None:
    widget = ChatMessageWidget("assistant", "Kısa cevap", "Arial", 11)
    qtbot.addWidget(widget)

    widget.set_bubble_width(760)

    assert widget.minimumWidth() == 760
    assert widget.bubble.minimumWidth() == 760
    assert widget.maximumWidth() == 760


def test_user_message_renders_image_preview_above_text(qtbot) -> None:
    image = QImage(320, 180, QImage.Format.Format_RGB32)
    image.fill(0x336699)
    data = QByteArray()
    buffer = QBuffer(data)
    assert buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    assert image.save(buffer, "PNG")
    buffer.close()
    widget = ChatMessageWidget(
        "user",
        "Bu görseli açıkla",
        "Arial",
        11,
        image_bytes=bytes(data),
    )
    qtbot.addWidget(widget)

    assert widget.image_label is not None
    assert widget.image_label.pixmap().isNull() is False
    assert widget.bubble.layout().indexOf(widget.image_label) < widget.bubble.layout().indexOf(
        widget.text_label
    )


def test_chat_message_uses_persisted_created_at(qtbot) -> None:
    widget = ChatMessageWidget(
        "assistant",
        "Eski cevap",
        "Arial",
        11,
        created_at=datetime(2020, 1, 2, 3, 4),
    )
    qtbot.addWidget(widget)

    expected = datetime(2020, 1, 2, 3, 4, tzinfo=timezone.utc).astimezone()
    assert widget.timestamp_label.text() == expected.strftime("%H:%M")


def test_visual_message_exposes_preview_and_reanalyze_actions(qtbot) -> None:
    image = QImage(320, 180, QImage.Format.Format_RGB32)
    image.fill(0x336699)
    data = QByteArray()
    buffer = QBuffer(data)
    assert buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    assert image.save(buffer, "PNG")
    buffer.close()
    context = _visual_context(bytes(data))
    widget = ChatMessageWidget(
        "user",
        "Bu görseli açıkla",
        "Arial",
        11,
        image_bytes=bytes(data),
        visual_context=context,
    )
    qtbot.addWidget(widget)
    widget.show()

    assert widget.reanalyze_button.isVisible() is True
    with qtbot.waitSignal(widget.reanalyze_requested, timeout=1000) as signal:
        widget.reanalyze_button.click()
    assert signal.args == [context]

    widget.set_visual_status("Analiz başarısız · Tekrar dene")
    assert widget.visual_status_label.text() == "Analiz başarısız · Tekrar dene"


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


def test_composer_is_compact_and_action_buttons_are_aligned(qtbot) -> None:
    composer = ComposerWidget("Arial", 11)
    qtbot.addWidget(composer)

    assert composer.input.minimumHeight() == COMPOSER_INPUT_MIN_HEIGHT
    assert composer.input.height() == COMPOSER_INPUT_MIN_HEIGHT
    assert composer.attachment_button.minimumHeight() == COMPOSER_BUTTON_HEIGHT
    assert composer.mic_button.minimumHeight() == COMPOSER_BUTTON_HEIGHT
    assert composer.screen_button.minimumHeight() == COMPOSER_BUTTON_HEIGHT
    assert composer.tools_button.minimumHeight() == COMPOSER_BUTTON_HEIGHT
    assert composer.send_button.minimumHeight() == COMPOSER_BUTTON_HEIGHT
    assert composer.input.parent() is composer
    assert composer.input_hint.text().startswith("Enter gönderir")
    assert composer.mic_button.isHidden()
    assert composer.screen_button.isHidden()
    assert composer.agent_button.isHidden()
    assert not composer.tools_button.isHidden()
    assert [action.text() for action in composer.tools_menu.actions()] == [
        "Mikrofon", "Ekran görüntüsü", "Agent modu"
    ]


def test_composer_compact_mode_and_agent_action(qtbot) -> None:
    composer = ComposerWidget("Arial", 11)
    qtbot.addWidget(composer)
    composer.set_compact(True)
    assert composer.input_hint.isHidden()
    assert composer.attachment_button.text() == "+"
    with qtbot.waitSignal(composer.agent_mode_requested, timeout=1000):
        composer.agent_button.click()


def test_composer_tools_menu_preserves_context_actions(qtbot) -> None:
    composer = ComposerWidget("Arial", 11)
    qtbot.addWidget(composer)
    with qtbot.waitSignal(composer.mic_requested, timeout=1000):
        composer.mic_action.trigger()
    with qtbot.waitSignal(composer.agent_mode_requested, timeout=1000):
        composer.agent_action.trigger()
    composer.set_mic_enabled(False)
    composer.set_screen_enabled(False)
    assert not composer.mic_action.isEnabled()
    assert not composer.screen_menu.menuAction().isEnabled()


def test_assistant_message_progressive_actions(qtbot) -> None:
    widget = ChatMessageWidget("assistant", "Yanıt", "Arial", 11)
    qtbot.addWidget(widget)
    assert widget.action_bar.isHidden()
    widget.action_bar.show()
    with qtbot.waitSignal(widget.read_aloud_requested, timeout=1000) as signal:
        widget.read_aloud_button.click()
    assert signal.args == ["Yanıt"]
    with qtbot.waitSignal(widget.retry_requested, timeout=1000):
        widget.retry_button.click()


def test_stream_preview_finalizes_one_message_widget(qtbot) -> None:
    widget = ChatMessageWidget("assistant", "Düşünüyor…", "Arial", 11, typing=True)
    qtbot.addWidget(widget)
    widget.update_stream_preview("İlk parça")
    assert widget.text_label.text() == "İlk parça"
    widget.finalize_stream("Kabul edilen final")
    assert widget.text_label.text() == "Kabul edilen final"
    assert not widget.typing


def test_welcome_state_has_non_persistent_prompt_suggestions(qtbot, tmp_path) -> None:
    welcome = WelcomeStateWidget(tmp_path / "missing.png")
    qtbot.addWidget(welcome)
    suggestions = welcome.findChildren(QPushButton, "suggestionButton")
    assert len(suggestions) == 3
    with qtbot.waitSignal(welcome.prompt_selected, timeout=1000) as signal:
        suggestions[1].click()
    assert "ajan" in signal.args[0]


def test_welcome_suggestions_stack_without_horizontal_overflow(qtbot, tmp_path) -> None:
    welcome = WelcomeStateWidget(tmp_path / "missing.png")
    qtbot.addWidget(welcome)
    welcome.resize(600, 500)
    welcome.show()
    qtbot.wait(10)

    positions = [welcome._suggestions.getItemPosition(index) for index in range(3)]
    assert [position[0] for position in positions] == [0, 1, 2]
    assert all(position[1] == 0 for position in positions)


def test_composer_screen_context_chip_can_be_shown_and_removed(qtbot) -> None:
    composer = ComposerWidget("Arial", 11)
    qtbot.addWidget(composer)

    composer.set_screen_context(1920, 1080)

    assert composer.screen_context_chip.isVisibleTo(composer)
    assert composer.screen_context_label.text() == "Ekran · 1920×1080"
    assert "kontrol ediliyor" in composer.screen_context_note.text()

    with qtbot.waitSignal(composer.screen_context_remove_requested, timeout=1000):
        composer.screen_context_remove_button.click()

    composer.clear_screen_context()
    assert composer.screen_context_chip.isHidden()
    assert composer.screen_context_label.text() == ""


def test_composer_attachment_controls_expose_preview_and_change(qtbot) -> None:
    composer = ComposerWidget("Arial", 11)
    qtbot.addWidget(composer)
    composer.set_screen_context(1920, 1080, image_bytes=b"not-an-image")

    assert composer.screen_context_thumbnail.isHidden() is True
    with qtbot.waitSignal(composer.screen_context_change_requested, timeout=1000):
        composer.screen_context_change_button.click()


def test_composer_waiting_state_keeps_input_enabled_and_shows_stop(qtbot) -> None:
    composer = ComposerWidget("Arial", 11)
    qtbot.addWidget(composer)
    composer.set_text("Yeni taslak")

    composer.set_waiting(True)

    assert composer.input.isEnabled() is True
    assert composer.send_button.text() == "Durdur"
    assert composer.send_button.isEnabled() is True

    with qtbot.waitSignal(composer.stop_requested, timeout=1000):
        composer.send_button.click()


def test_composer_restores_send_button_after_waiting(qtbot) -> None:
    composer = ComposerWidget("Arial", 11)
    qtbot.addWidget(composer)
    composer.set_text("Merhaba")

    composer.set_waiting(True)
    composer.set_waiting(False)

    assert composer.send_button.text() == "Gönder"
    assert composer.input.isEnabled() is True
    assert composer.send_button.isEnabled() is True


def test_composer_multiline_growth_is_bounded(qtbot) -> None:
    composer = ComposerWidget("Arial", 11)
    qtbot.addWidget(composer)

    composer.set_text("\n".join(str(index) for index in range(20)))

    assert composer.input.height() <= COMPOSER_INPUT_MAX_HEIGHT


def test_composer_first_character_does_not_expand_height(qtbot) -> None:
    composer = ComposerWidget("Arial", 11)
    qtbot.addWidget(composer)
    initial_height = composer.input.height()

    qtbot.keyClicks(composer.input, "a")

    assert composer.input.height() == initial_height


def test_composer_grows_with_new_lines_and_shrinks_when_cleared(qtbot) -> None:
    composer = ComposerWidget("Arial", 11)
    qtbot.addWidget(composer)
    initial_height = composer.input.height()

    composer.set_text("bir\niki\nüç")

    assert composer.input.height() > initial_height

    composer.clear()

    assert composer.input.height() == COMPOSER_INPUT_MIN_HEIGHT


def test_composer_enables_scrollbar_after_max_height(qtbot) -> None:
    composer = ComposerWidget("Arial", 11)
    qtbot.addWidget(composer)

    composer.set_text("\n".join(str(index) for index in range(40)))

    assert composer.input.height() == COMPOSER_INPUT_MAX_HEIGHT
    assert composer.input.verticalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAsNeeded


def test_transcription_append_recalculates_composer_height(qtbot) -> None:
    composer = ComposerWidget("Arial", 11)
    qtbot.addWidget(composer)

    assert composer.append_transcription("bir\niki") is True

    assert composer.input.height() > COMPOSER_INPUT_MIN_HEIGHT


def test_sidebar_has_collapsible_product_navigation_without_font_controls(qtbot, tmp_path) -> None:
    sidebar = SidebarWidget(tmp_path / "missing.png", "v0.test", "llama3")
    qtbot.addWidget(sidebar)

    assert sidebar.width() == SidebarWidget.WIDTH
    assert sidebar.logo_label.text() == "L"
    assert not hasattr(sidebar, "font_decrease_button")
    assert not hasattr(sidebar, "font_increase_button")
    assert sidebar.collapse_button.accessibleName() == "Sol navigasyonu daralt"
    assert "Veriler cihazında" in sidebar.local_status.text()
    assert sidebar.session_scroll.objectName() == "sidebarConversationScroll"
    assert sidebar.session_scroll.viewport().objectName() == "sidebarConversationViewport"
    assert sidebar.session_list.objectName() == "sidebarConversationList"
    assert sidebar.subtitle_label.isHidden()
    assert sidebar.filter_combo.isHidden()
    assert sidebar.status_panel.isHidden()
    assert sidebar.shortcuts.isHidden()

    with qtbot.waitSignal(sidebar.collapsed_changed, timeout=1000) as signal:
        sidebar.collapse_button.click()
    assert signal.args == [True]
    assert sidebar.width() == SidebarWidget.COLLAPSED_WIDTH
    assert sidebar.session_panel.isHidden()
    assert sidebar.new_chat_button.toolTip() == "Yeni sohbet"

    sidebar.set_collapsed(False)
    assert sidebar.width() == SidebarWidget.WIDTH


def test_sidebar_renders_persisted_sessions_and_active_state(qtbot, tmp_path) -> None:
    sidebar = SidebarWidget(tmp_path / "missing.png", "v0.test", "llama3")
    qtbot.addWidget(sidebar)
    timestamp = datetime.now()
    sessions = (
        ConversationSession(1, "İlk Sohbet", timestamp, timestamp, timestamp),
        ConversationSession(2, "İkinci Sohbet", timestamp, timestamp, timestamp),
    )

    sidebar.set_sessions(sessions, active_id=2)

    buttons = sidebar.session_list.findChildren(type(sidebar.new_chat_button))
    session_buttons = [button for button in buttons if button.objectName() == "sessionButton"]
    assert [button.toolTip() for button in session_buttons] == ["İlk Sohbet", "İkinci Sohbet"]
    assert session_buttons[1].text() != ""
    assert session_buttons[1].isChecked() is True
    assert all(button.minimumHeight() == 56 for button in session_buttons)
    assert "·" in session_buttons[0].text()


def test_sidebar_search_and_filter_controls_are_accessible(qtbot, tmp_path) -> None:
    sidebar = SidebarWidget(tmp_path / "missing.png", "v0.test", "llama3")
    qtbot.addWidget(sidebar)

    sidebar.search_input.setText("vision")
    assert sidebar.search_input.accessibleName() == "Sohbetlerde ara"
    assert sidebar.filter_combo.currentData() == "chats"
    sidebar.filter_combo.setCurrentIndex(2)
    assert sidebar.filter_combo.currentData() == "archive"

    sidebar.search_input.clear()
    assert sidebar.search_input.text() == ""


def test_sidebar_search_results_show_safe_plain_text_snippet(qtbot, tmp_path) -> None:
    sidebar = SidebarWidget(tmp_path / "missing.png", "v0.test", "llama3")
    qtbot.addWidget(sidebar)
    now = datetime.now(timezone.utc)
    sidebar.set_search_results(
        (
            ConversationSearchResult(
                conversation_id=1,
                title="Vision sohbeti",
                snippet="Görsel sonucu",
                matched_at=now,
                matched_role="user",
                match_type="message",
                last_activity_at=now,
            ),
        )
    )

    results = sidebar.session_list.findChildren(type(sidebar.new_chat_button), "conversationSearchResult")
    assert len(results) == 1
    assert "Görsel sonucu" in results[0].text()
