"""Small reusable Tkinter components for Lina's desktop interface."""

from __future__ import annotations

import tkinter as tk
from typing import Any

from lina.interfaces.gui_theme import (
    COLOR_BORDER,
    COLOR_PANEL_BG,
    COLOR_TEXT_PRIMARY,
)


class Tooltip:
    """Show a compact text tooltip for a Tkinter widget."""

    def __init__(self, widget: Any, text: str, delay_ms: int = 450) -> None:
        self._widget = widget
        self._text = text
        self._delay_ms = delay_ms
        self._after_id = None
        self._window: tk.Toplevel | None = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, event=None) -> None:
        self._cancel_schedule()
        self._after_id = self._widget.after(self._delay_ms, self._show)

    def _show(self) -> None:
        self._after_id = None
        if self._window is not None:
            return
        try:
            x = self._widget.winfo_rootx() + 8
            y = self._widget.winfo_rooty() + self._widget.winfo_height() + 8
            window = tk.Toplevel(self._widget)
            window.wm_overrideredirect(True)
            window.wm_geometry(f"+{x}+{y}")
            label = tk.Label(
                window,
                text=self._text,
                bg=COLOR_PANEL_BG,
                fg=COLOR_TEXT_PRIMARY,
                relief=tk.SOLID,
                borderwidth=1,
                highlightbackground=COLOR_BORDER,
                padx=8,
                pady=5,
            )
            label.pack()
            self._window = window
        except tk.TclError:
            self._window = None

    def _hide(self, event=None) -> None:
        self._cancel_schedule()
        if self._window is None:
            return
        try:
            self._window.destroy()
        except tk.TclError:
            pass
        self._window = None

    def _cancel_schedule(self) -> None:
        if self._after_id is None:
            return
        try:
            self._widget.after_cancel(self._after_id)
        except tk.TclError:
            pass
        self._after_id = None
