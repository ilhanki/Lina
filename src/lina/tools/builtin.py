"""Safe built-in tools for Lina."""

from dataclasses import dataclass
from datetime import datetime

from lina.tools.permissions import PermissionLevel
from lina.tools.tool import ToolResult


@dataclass(frozen=True)
class EchoTool:
    """A safe tool that returns the provided input text."""

    name: str = "echo"
    description: str = "Returns the provided input text."
    permission_level: PermissionLevel = PermissionLevel.SAFE

    def execute(self, input_text: str = "") -> ToolResult:
        return ToolResult(text=input_text)


@dataclass(frozen=True)
class CurrentTimeTool:
    """A safe tool that returns the current local time."""

    name: str = "current_time"
    description: str = "Returns the current local time."
    permission_level: PermissionLevel = PermissionLevel.SAFE
    clock: object = datetime.now

    def execute(self, input_text: str = "") -> ToolResult:
        current_time = self.clock()
        return ToolResult(text=f"Şu an saat {current_time:%H:%M}.")
