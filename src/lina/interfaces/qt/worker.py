"""Small signal-based background worker for the Qt interface."""

from __future__ import annotations

from collections.abc import Callable
import threading
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
        self._cancelled = threading.Event()
        self.signals = WorkerSignals()

    def cancel(self) -> None:
        """Suppress late result/error delivery; the owned service stops actual I/O."""
        self._cancelled.set()

    @property
    def cancelled(self) -> bool:
        return self._cancelled.is_set()

    @Slot()
    def run(self) -> None:
        if self.cancelled:
            self.signals.finished.emit()
            return
        try:
            result = self._function(*self._args)
        except Exception as error:
            if not self.cancelled:
                self.signals.error.emit(error)
        else:
            if not self.cancelled:
                self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()
