"""Tool contracts for Lina."""

from dataclasses import dataclass
from typing import Protocol

from lina.tools.permissions import PermissionLevel


@dataclass(frozen=True)
class ToolResult:
    """Result returned by a tool execution."""

    text: str


class Tool(Protocol):
    """Contract implemented by Lina tools."""

    @property
    def name(self) -> str:
        """Unique tool name."""

    @property
    def description(self) -> str:
        """Human-readable tool description."""

    @property
    def permission_level(self) -> PermissionLevel:
        """Permission required by this tool."""

    def execute(self, input_text: str = "") -> ToolResult:
        """Execute the tool."""
