"""Tool registry for Lina."""

from lina.tools.tool import Tool


class ToolRegistryError(Exception):
    """Raised when tool registry operations fail."""


class ToolRegistry:
    """Stores tools by unique name."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ToolRegistryError(f"Tool already registered: {tool.name}")

        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        try:
            return self._tools[name]
        except KeyError as error:
            raise ToolRegistryError(f"Unknown tool: {name}") from error

    def list_names(self) -> tuple[str, ...]:
        return tuple(sorted(self._tools))
