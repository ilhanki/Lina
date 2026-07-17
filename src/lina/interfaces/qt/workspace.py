"""Progressive-disclosure workspace surfaces for the redesigned app shell."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout,
)

from lina.interfaces.qt.context_inspector import ContextInspector


@dataclass(frozen=True, slots=True)
class PaletteAction:
    id: str
    title: str
    keywords: str
    callback: Callable[[], None]
    available: bool = True


DetailsInspector = ContextInspector


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
