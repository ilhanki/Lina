"""Tests for reusable GUI components."""

from lina.interfaces.gui_components import Tooltip


class FakeWidget:
    def __init__(self) -> None:
        self.bindings = {}
        self.after_calls = []
        self.cancelled = []

    def bind(self, event: str, callback, add: str) -> None:
        self.bindings[event] = (callback, add)

    def after(self, delay_ms: int, callback):
        self.after_calls.append((delay_ms, callback))
        return "after-id"

    def after_cancel(self, after_id: str) -> None:
        self.cancelled.append(after_id)


def test_tooltip_binds_hover_and_click_events() -> None:
    widget = FakeWidget()

    Tooltip(widget, "Mesajı gönder")

    assert set(widget.bindings) == {"<Enter>", "<Leave>", "<ButtonPress>"}
    assert all(add == "+" for _, add in widget.bindings.values())


def test_tooltip_schedules_and_cancels_display() -> None:
    widget = FakeWidget()
    tooltip = Tooltip(widget, "Mesajı gönder", delay_ms=300)

    tooltip._schedule()
    tooltip._hide()

    assert widget.after_calls[0][0] == 300
    assert widget.cancelled == ["after-id"]
