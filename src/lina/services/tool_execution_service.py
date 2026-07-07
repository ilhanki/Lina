"""Safe tool execution service for Lina."""

from lina.tools.permissions import can_execute_automatically
from lina.tools.registry import ToolRegistry, ToolRegistryError
from lina.tools.tool import ToolResult


class ToolExecutionError(Exception):
    """Raised when a tool cannot be executed safely."""


class ToolExecutionService:
    """Executes registered tools within permission limits."""

    def __init__(self, tool_registry: ToolRegistry) -> None:
        self._tool_registry = tool_registry

    def execute(self, tool_name: str, input_text: str = "") -> ToolResult:
        try:
            tool = self._tool_registry.get(tool_name)
        except ToolRegistryError as error:
            raise ToolExecutionError(f"Tool is not available: {tool_name}") from error

        if not can_execute_automatically(tool.permission_level):
            raise ToolExecutionError(
                f"Tool cannot be executed automatically: {tool_name}"
            )

        return tool.execute(input_text=input_text)
