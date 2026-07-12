"""Tests for PySide6 GUI widgets."""

from datetime import datetime, timezone

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, Qt
from PySide6.QtGui import QImage

from lina.interfaces.qt.theme import clamp_message_font_size, resolve_font_family
from lina.interfaces.qt.widgets import ChatMessageWidget, ComposerWidget, SidebarWidget
from lina.interfaces.qt.widgets.chat_message import MIN_BUBBLE_WIDTH
from lina.interfaces.qt.widgets.composer import (
    COMPOSER_BUTTON_HEIGHT,
    COMPOSER_INPUT_MAX_HEIGHT,
    COMPOSER_INPUT_MIN_HEIGHT,
)
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
    assert widget.copy_button.parent() is widget.bubble


def test_chat_message_uses_natural_minimum_bubble_width(qtbot) -> None:
    widget = ChatMessageWidget("assistant", "Kısa cevap", "Arial", 11)
    qtbot.addWidget(widget)

    widget.set_bubble_width(760)

    assert widget.minimumWidth() == MIN_BUBBLE_WIDTH
    assert widget.bubble.minimumWidth() == MIN_BUBBLE_WIDTH
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
    assert composer.send_button.minimumHeight() == COMPOSER_BUTTON_HEIGHT


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


def test_sidebar_is_simplified_without_collapse_or_font_controls(qtbot, tmp_path) -> None:
    sidebar = SidebarWidget(tmp_path / "missing.png", "v0.test", "llama3")
    qtbot.addWidget(sidebar)

    assert sidebar.width() == SidebarWidget.WIDTH
    assert sidebar.logo_label.text() == "L"
    assert not hasattr(sidebar, "font_decrease_button")
    assert not hasattr(sidebar, "font_increase_button")
    assert not hasattr(sidebar, "collapse_button")
    assert "Veriler cihazında" in sidebar.local_status.text()


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
    assert all(button.minimumHeight() == 64 for button in session_buttons)
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
