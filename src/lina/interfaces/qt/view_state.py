"""Typed, presentation-only state for Lina's responsive application shell."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from lina.ui.design import LayoutMetrics


class ResponsiveMode(Enum):
    LARGE = "large"
    MEDIUM = "medium"
    COMPACT = "compact"


class RightPanelSection(Enum):
    TOOLS = "tools"
    MEMORY = "memory"
    AGENT = "agent"
    VOICE = "voice"
    VISION = "vision"
    SYSTEM = "system"


@dataclass(frozen=True, slots=True)
class ApplicationViewState:
    sidebar_collapsed: bool = False
    right_panel_visible: bool = True
    right_panel_section: RightPanelSection = RightPanelSection.TOOLS
    responsive_mode: ResponsiveMode = ResponsiveMode.LARGE
    conversation_id: int | None = None
    unified_status: str = "Hazır"
    theme: str = "dark"

    def for_width(self, width: int, layout: LayoutMetrics) -> "ApplicationViewState":
        if width < layout.compact_breakpoint:
            mode = ResponsiveMode.COMPACT
        elif width < layout.medium_breakpoint:
            mode = ResponsiveMode.MEDIUM
        else:
            mode = ResponsiveMode.LARGE
        return replace(
            self,
            responsive_mode=mode,
            sidebar_collapsed=mode is ResponsiveMode.COMPACT,
            right_panel_visible=self.right_panel_visible if mode is ResponsiveMode.LARGE else False,
        )
