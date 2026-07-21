from datetime import datetime

from lina.interfaces.qt.workspace import CommandPalette, DetailsInspector, PaletteAction
from lina.memory.models import MemoryRecord, MemoryType
from lina.services.local_storage_service import LocalStorageSnapshot
from PySide6.QtWidgets import QLabel, QPushButton


def test_inspector_is_progressive_and_accessible(qtbot):
    inspector = DetailsInspector()
    qtbot.addWidget(inspector)
    inspector.show_details("Agent Görevi", "İki adım tamamlandı.")
    assert inspector.title.text() == "Agent Görevi"
    assert inspector.summary.text() == "İki adım tamamlandı."
    assert inspector.accessibleName() == "Bağlamsal araçlar paneli"
    widget = QLabel("Typed içerik")
    inspector.show_widget("Teknik Durum", widget)
    assert inspector.summary.isHidden()
    assert inspector.content.count() == 1


def test_context_inspector_exposes_real_tool_routes_and_memory(qtbot):
    class MemoryStub:
        def list_memories(self):
            now = datetime.now()
            return (
                MemoryRecord(1, MemoryType.USER_PREFERENCE, "Koyu temayı tercih ediyor.", now, now, "test"),
                MemoryRecord(2, MemoryType.USER_PREFERENCE, "Şifrem gizli", now, now, "test"),
            )

        def is_sensitive_content(self, content):
            return "şifre" in content.casefold()

    inspector = DetailsInspector(MemoryStub(), "llama3.2:3b")
    qtbot.addWidget(inspector)
    assert tuple(inspector.tools_panel.rows) == (
        "chat", "voice", "vision", "file", "reminders", "memory", "agent", "codex"
    )
    assert inspector.tools_panel.rows["chat"]._grid_position == (0, 0)
    assert inspector.tools_panel.rows["memory"]._grid_position == (2, 1)
    assert inspector.tools_panel.rows["voice"].minimumHeight() == 112
    assert inspector.tools_panel.rows["agent"].isHidden()
    assert inspector.tools_panel.rows["codex"].isHidden()
    inspector.set_advanced_tools_visible(agent=True, codex=False)
    requested = []
    inspector.tool_requested.connect(requested.append)
    inspector.tools_panel.rows["agent"].click()
    assert requested == ["agent"]
    assert inspector.memory_panel.items.count() == 1
    inspector.set_storage_snapshot(LocalStorageSnapshot(2048, 2, ()))
    assert "2.0 KB" in inspector.local_panel.storage_label.text()
    inspector.memory_panel.refresh()
    assert inspector.memory_panel.items.count() == 1
    assert len([
        button for button in inspector.memory_panel.findChildren(QPushButton)
        if "Koyu temayı" in button.text() and not button.isHidden()
    ]) <= 1


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
