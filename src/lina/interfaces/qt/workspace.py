"""Progressive-disclosure workspace surfaces for the redesigned app shell."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QVBoxLayout, QWidget,
)
from lina.ui.design import standard_icon


@dataclass(frozen=True, slots=True)
class PaletteAction:
    id: str
    title: str
    keywords: str
    callback: Callable[[], None]
    available: bool = True


class DetailsInspector(QWidget):
    closed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("detailsInspector")
        self.setAccessibleName("Ayrıntılar paneli")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        header = QHBoxLayout()
        self.title = QLabel("Ayrıntılar", self)
        self.title.setObjectName("inspectorTitle")
        header.addWidget(self.title, 1)
        self.close_button = QPushButton("Kapat", self)
        self.close_button.setObjectName("iconButton")
        self.close_button.setToolTip("Ayrıntılar panelini kapat")
        self.close_button.setAccessibleName("Ayrıntıları kapat")
        self.close_button.setIcon(standard_icon(self, "close"))
        header.addWidget(self.close_button)
        layout.addLayout(header)
        self.summary = QLabel("Aktif görev veya oturum ayrıntıları burada görünür.", self)
        self.summary.setObjectName("mutedLabel")
        self.summary.setWordWrap(True)
        self.summary.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.summary)
        self.content = QVBoxLayout()
        layout.addLayout(self.content)
        layout.addStretch(1)
        self.close_button.clicked.connect(self.closed)

    def show_details(self, title: str, summary: str) -> None:
        self._clear_content()
        self.title.setText(title)
        self.summary.show()
        self.summary.setText(summary)
        self.show()

    def show_widget(self, title: str, widget: QWidget) -> None:
        self._clear_content()
        self.title.setText(title)
        self.summary.hide()
        widget.setParent(self)
        self.content.addWidget(widget)
        self.show()

    def _clear_content(self) -> None:
        while self.content.count():
            item = self.content.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()


class CommandPalette(QDialog):
    """Keyboard-first launcher; actions remain owned by the main window."""

    def __init__(self, actions: tuple[PaletteAction, ...], parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("commandPalette")
        self.setWindowTitle("Komut Paleti")
        self.setModal(True)
        self.resize(560, 420)
        self._actions = actions
        layout = QVBoxLayout(self)
        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Bir eylem ara…")
        self.search.setAccessibleName("Komut ara")
        layout.addWidget(self.search)
        self.results = QListWidget(self)
        self.results.setAccessibleName("Kullanılabilir komutlar")
        layout.addWidget(self.results, 1)
        self.search.textChanged.connect(self._filter)
        self.search.returnPressed.connect(self._execute_current)
        self.results.itemActivated.connect(lambda _item: self._execute_current())
        self._filter("")

    def open_focused(self) -> None:
        self._filter("")
        self.search.clear()
        self.open()
        self.search.setFocus()

    def _filter(self, query: str) -> None:
        needle = " ".join(query.casefold().split())
        self.results.clear()
        for index, action in enumerate(self._actions):
            haystack = f"{action.title} {action.keywords}".casefold()
            if needle and needle not in haystack:
                continue
            item = QListWidgetItem(action.title)
            item.setData(Qt.ItemDataRole.UserRole, index)
            if not action.available:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                item.setToolTip("Bu eylem şu anda kullanılamıyor")
            self.results.addItem(item)
        if self.results.count():
            self.results.setCurrentRow(0)

    def _execute_current(self) -> None:
        item = self.results.currentItem()
        if item is None or not item.flags() & Qt.ItemFlag.ItemIsEnabled:
            return
        action = self._actions[int(item.data(Qt.ItemDataRole.UserRole))]
        self.accept()
        action.callback()
