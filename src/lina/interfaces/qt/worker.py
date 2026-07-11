"""Small signal-based background worker for the Qt interface."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class WorkerSignals(QObject):
    """Signals emitted by a one-shot worker."""

    result = Signal(object)
    error = Signal(object)
    finished = Signal()


class FunctionWorker(QRunnable):
    """Execute one callable outside the GUI thread."""

    def __init__(self, function: Callable[..., Any], *args: Any) -> None:
        super().__init__()
        self._function = function
        self._args = args
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            result = self._function(*self._args)
        except Exception as error:
            self.signals.error.emit(error)
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()
