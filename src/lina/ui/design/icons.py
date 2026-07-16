"""Theme-aware Qt standard icons without bundled brand assets or emoji controls."""

from __future__ import annotations

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QStyle, QWidget


_STANDARD = {
    "add": QStyle.StandardPixmap.SP_FileDialogNewFolder,
    "search": QStyle.StandardPixmap.SP_FileDialogContentsView,
    "settings": QStyle.StandardPixmap.SP_FileDialogDetailedView,
    "notifications": QStyle.StandardPixmap.SP_MessageBoxInformation,
    "details": QStyle.StandardPixmap.SP_FileDialogInfoView,
    "close": QStyle.StandardPixmap.SP_DialogCloseButton,
    "send": QStyle.StandardPixmap.SP_ArrowForward,
    "microphone": QStyle.StandardPixmap.SP_MediaPlay,
    "screen": QStyle.StandardPixmap.SP_ComputerIcon,
    "agent": QStyle.StandardPixmap.SP_CommandLink,
}


def standard_icon(widget: QWidget, name: str) -> QIcon:
    try:
        pixmap = _STANDARD[name]
    except KeyError as error:
        raise ValueError(f"Unknown interface icon: {name}") from error
    return widget.style().standardIcon(pixmap)
