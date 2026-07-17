from lina.interfaces.qt.workspace import CommandPalette, DetailsInspector, PaletteAction
from PySide6.QtWidgets import QLabel


def test_inspector_is_progressive_and_accessible(qtbot):
    inspector = DetailsInspector()
    qtbot.addWidget(inspector)
    inspector.show_details("Agent Görevi", "İki adım tamamlandı.")
    assert inspector.title.text() == "Agent Görevi"
    assert inspector.summary.text() == "İki adım tamamlandı."
    assert inspector.accessibleName() == "Ayrıntılar paneli"
    widget = QLabel("Typed içerik")
    inspector.show_widget("Teknik Durum", widget)
    assert inspector.summary.isHidden()
    assert inspector.content.count() == 1


def test_command_palette_filters_and_executes_keyboard_action(qtbot):
    called = []
    palette = CommandPalette((
        PaletteAction("new", "Yeni sohbet", "sohbet", lambda: called.append("new")),
        PaletteAction("settings", "Ayarlar", "tema", lambda: called.append("settings")),
    ))
    qtbot.addWidget(palette)
    palette.search.setText("tema")
    assert palette.results.count() == 1
    palette._execute_current()
    assert called == ["settings"]


def test_command_palette_marks_unavailable_actions(qtbot):
    palette = CommandPalette((PaletteAction("camera", "Kamera", "vision", lambda: None, False),))
    qtbot.addWidget(palette)
    palette.results.setCurrentRow(0)
    palette._execute_current()
    assert palette.result() == 0
