"""Qt-thread bridges used by framework-neutral live vision sources."""

from __future__ import annotations

from collections.abc import Callable
import threading

from PySide6.QtCore import QObject, Qt, Signal, Slot


class QtCaptureInvoker(QObject):
    """Run a QScreen capture callable on the object's GUI thread."""

    requested = Signal()

    def __init__(self, capture: Callable[[], object], parent=None) -> None:
        super().__init__(parent)
        self._capture = capture
        self._result = None
        self._error: Exception | None = None
        self._lock = threading.Lock()
        self.requested.connect(self._execute, Qt.ConnectionType.BlockingQueuedConnection)

    def capture(self):
        with self._lock:
            self._result = None
            self._error = None
            self.requested.emit()
            if self._error is not None:
                raise self._error
            return self._result

    @Slot()
    def _execute(self) -> None:
        try:
            self._result = self._capture()
        except Exception as error:
            self._error = error
