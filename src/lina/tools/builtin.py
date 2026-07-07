"""Safe built-in tools for Lina."""

from dataclasses import dataclass

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
