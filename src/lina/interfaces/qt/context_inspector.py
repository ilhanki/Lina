"""Contextual tools, memory, and local-status third column."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from lina.memory.service import MemoryService
from lina.services.local_storage_service import LocalStorageSnapshot, format_storage_size
from lina.ui.design import standard_icon


@dataclass(frozen=True, slots=True)
class ContextTool:
    id: str
    title: str
    description: str
    icon: str


CORE_CONTEXT_TOOLS = (
    ContextTool("voice", "Sesli Mod", "Doğal sesli sohbet", "voice"),
    ContextTool("vision", "Görsel Anlama", "Ekran, görsel ve diyagram analizi", "vision"),
    ContextTool("file", "Dosya Anlama", "Desteklenen yerel dosyaları incele", "file"),
)

ADVANCED_CONTEXT_TOOLS = (
    ContextTool("agent", "Agent", "Planla, uygula ve doğrula", "agent"),
    ContextTool("codex", "Codex ile Çalış", "Güvenli, kontrollü proje çalışması", "agent"),
)


class DrawerScrim(QWidget):
    clicked = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("drawerScrim")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAccessibleName("Sağ panel arka planı")

    def mousePressEvent(self, event) -> None:
        self.clicked.emit()
        event.accept()


class ToolsPanel(QFrame):
    tool_requested = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("contextSection")
        self.setMinimumHeight(410)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        heading = QLabel("Araçlar", self)
        heading.setObjectName("inspectorSectionTitle")
        layout.addWidget(heading)
        self.rows: dict[str, QPushButton] = {}
        for tool in (*CORE_CONTEXT_TOOLS, *ADVANCED_CONTEXT_TOOLS):
            button = QPushButton(f"{tool.title}\n{tool.description}", self)
            button.setObjectName("contextToolRow")
            button.setIcon(standard_icon(self, tool.icon, 20))
            button.setAccessibleName(tool.title)
            button.setAccessibleDescription(tool.description)
            button.setToolTip(f"{tool.title}: {tool.description}")
            button.clicked.connect(
                lambda _checked=False, tool_id=tool.id: self.tool_requested.emit(tool_id)
            )
            layout.addWidget(button)
            self.rows[tool.id] = button
        self.set_advanced_tools_visible(agent=False, codex=False)

    def set_advanced_tools_visible(self, *, agent: bool, codex: bool) -> None:
        """Keep optional project automation out of the primary tool surface."""
        self.rows["agent"].setVisible(agent)
        self.rows["codex"].setVisible(codex)


class MemoryPanel(QFrame):
    memory_requested = Signal()

    def __init__(self, memory_service: MemoryService | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("contextSection")
        self.setMinimumHeight(132)
        self._memory_service = memory_service
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        header = QHBoxLayout()
        title = QLabel("Bellek", self)
        title.setObjectName("inspectorSectionTitle")
        header.addWidget(title, 1)
        self.show_all_button = QPushButton("Tümünü Gör", self)
        self.show_all_button.setObjectName("inspectorLinkButton")
        self.show_all_button.setAccessibleName("Tüm bellek kayıtlarını göster")
        self.show_all_button.clicked.connect(self.memory_requested)
        header.addWidget(self.show_all_button)
        layout.addLayout(header)
        note = QLabel("Lina’nın senin için önemli bulduğu bilgiler.", self)
        note.setObjectName("inspectorDescription")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.items = QVBoxLayout()
        self.items.setSpacing(6)
        layout.addLayout(self.items)
        self.refresh()

    def refresh(self) -> None:
        while self.items.count():
            item = self.items.takeAt(0)
            if item.widget() is not None:
                item.widget().hide()
                item.widget().deleteLater()
        if self._memory_service is None:
            self._add_empty("Bellek bu çalışma alanında etkin değil.")
            self.show_all_button.setEnabled(False)
            return
        memories = tuple(
            memory
            for memory in self._memory_service.list_memories()
            if not self._memory_service.is_sensitive_content(memory.content)
        )[:4]
        if not memories:
            self._add_empty("Henüz kayıtlı bir bilgi yok.")
            return
        for memory in memories:
            summary = " ".join(memory.content.split())
            if len(summary) > 96:
                summary = summary[:93].rstrip() + "…"
            card = QPushButton(summary, self)
            card.setObjectName("memoryCard")
            card.setToolTip("Bellek görünümünü aç")
            card.setAccessibleName(f"Bellek kaydı: {summary}")
            card.clicked.connect(self.memory_requested)
            self.items.addWidget(card)

    def _add_empty(self, text: str) -> None:
        label = QLabel(text, self)
        label.setObjectName("inspectorEmptyState")
        label.setWordWrap(True)
        self.items.addWidget(label)


class LocalStatusPanel(QFrame):
    data_folder_requested = Signal()

    def __init__(self, model_name: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("contextSection")
        self.setMinimumHeight(152)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)
        title = QLabel("Yerel çalışma", self)
        title.setObjectName("inspectorSectionTitle")
        layout.addWidget(title)
        self.model_label = QLabel(f"Model · {model_name}", self)
        self.model_label.setObjectName("inspectorDescription")
        self.model_label.setWordWrap(True)
        layout.addWidget(self.model_label)
        self.storage_label = QLabel("Yerel depolama hesaplanıyor…", self)
        self.storage_label.setObjectName("inspectorDescription")
        layout.addWidget(self.storage_label)
        self.open_button = QPushButton("Veri Klasörünü Aç", self)
        self.open_button.setObjectName("secondaryButton")
        self.open_button.setAccessibleName("Yerel veri klasörünü aç")
        self.open_button.clicked.connect(self.data_folder_requested)
        layout.addWidget(self.open_button)

    def set_snapshot(self, snapshot: LocalStorageSnapshot) -> None:
        suffix = " · ölçüm sınırlandı" if snapshot.truncated else ""
        self.storage_label.setText(
            f"Yerel depolama · {format_storage_size(snapshot.total_bytes)} · "
            f"{snapshot.file_count} dosya{suffix}"
        )
        self.open_button.setEnabled(bool(snapshot.locations))


class ContextInspector(QWidget):
    closed = Signal()
    tool_requested = Signal(str)
    memory_requested = Signal()
    data_folder_requested = Signal()

    def __init__(
        self,
        memory_service: MemoryService | None = None,
        model_name: str = "model bilinmiyor",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("detailsInspector")
        self.setAccessibleName("Bağlamsal araçlar paneli")
        self.display_mode = "docked"
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        header = QHBoxLayout()
        self.title = QLabel("Araçlar", self)
        self.title.setObjectName("inspectorTitle")
        header.addWidget(self.title, 1)
        self.close_button = QPushButton("", self)
        self.close_button.setObjectName("iconButton")
        self.close_button.setToolTip("Sağ paneli kapat · Esc")
        self.close_button.setAccessibleName("Sağ paneli kapat")
        self.close_button.setIcon(standard_icon(self, "close", 18))
        header.addWidget(self.close_button)
        layout.addLayout(header)

        self.pages = QStackedWidget(self)
        self.pages.setObjectName("inspectorPages")
        self.home_scroll = QScrollArea(self.pages)
        self.home_scroll.setObjectName("inspectorScroll")
        self.home_scroll.setWidgetResizable(True)
        home = QWidget(self.home_scroll)
        home.setObjectName("inspectorHome")
        home_layout = QVBoxLayout(home)
        home_layout.setContentsMargins(0, 0, 0, 0)
        home_layout.setSpacing(20)
        home_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.tools_panel = ToolsPanel(home)
        self.memory_panel = MemoryPanel(memory_service, home)
        self.local_panel = LocalStatusPanel(model_name, home)
        home_layout.addWidget(self.tools_panel)
        home_layout.addWidget(self.memory_panel)
        home_layout.addWidget(self.local_panel)
        home_layout.addStretch(1)
        self.home_scroll.setWidget(home)
        self.pages.addWidget(self.home_scroll)

        self.detail_page = QWidget(self.pages)
        detail_layout = QVBoxLayout(self.detail_page)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(10)
        self.back_button = QPushButton("‹ Araçlara Dön", self.detail_page)
        self.back_button.setObjectName("inspectorLinkButton")
        self.back_button.setAccessibleName("Araçlar paneline dön")
        detail_layout.addWidget(self.back_button)
        self.summary = QLabel("", self.detail_page)
        self.summary.setObjectName("inspectorDescription")
        self.summary.setWordWrap(True)
        self.summary.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        detail_layout.addWidget(self.summary)
        self.content = QVBoxLayout()
        detail_layout.addLayout(self.content)
        detail_layout.addStretch(1)
        self.pages.addWidget(self.detail_page)
        layout.addWidget(self.pages, 1)

        self.close_button.clicked.connect(self.closed)
        self.back_button.clicked.connect(self.show_home)
        self.tools_panel.tool_requested.connect(self.tool_requested)
        self.memory_panel.memory_requested.connect(self.memory_requested)
        self.local_panel.data_folder_requested.connect(self.data_folder_requested)

    def show_home(self) -> None:
        self._clear_content()
        self.title.setText("Araçlar")
        self.memory_panel.refresh()
        self.pages.setCurrentWidget(self.home_scroll)
        self.show()

    def show_details(self, title: str, summary: str) -> None:
        self._clear_content()
        self.title.setText(title)
        self.summary.show()
        self.summary.setText(summary)
        self.pages.setCurrentWidget(self.detail_page)
        self.show()

    def show_widget(self, title: str, widget: QWidget) -> None:
        self._clear_content()
        self.title.setText(title)
        self.summary.hide()
        widget.setParent(self.detail_page)
        self.content.addWidget(widget)
        self.pages.setCurrentWidget(self.detail_page)
        self.show()

    def set_storage_snapshot(self, snapshot: LocalStorageSnapshot) -> None:
        self.local_panel.set_snapshot(snapshot)

    def set_advanced_tools_visible(self, *, agent: bool, codex: bool) -> None:
        self.tools_panel.set_advanced_tools_visible(agent=agent, codex=codex)

    def _clear_content(self) -> None:
        while self.content.count():
            item = self.content.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.deleteLater()
