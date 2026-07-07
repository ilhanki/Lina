from dataclasses import dataclass

import pytest

from lina.tools.permissions import PermissionLevel
from lina.tools.registry import ToolRegistry, ToolRegistryError
from lina.tools.tool import ToolResult


@dataclass(frozen=True)
class FakeTool:
    name: str
    description: str = "Fake tool"
    permission_level: PermissionLevel = PermissionLevel.SAFE

    def execute(self, input_text: str = "") -> ToolResult:
        return ToolResult(text=input_text)


def test_tool_registry_registers_and_returns_tool() -> None:
    registry = ToolRegistry()
    tool = FakeTool(name="echo")

    registry.register(tool)

    assert registry.get("echo") is tool


def test_tool_registry_rejects_duplicate_tools() -> None:
    registry = ToolRegistry()
    registry.register(FakeTool(name="echo"))

    with pytest.raises(ToolRegistryError, match="already registered"):
        registry.register(FakeTool(name="echo"))


def test_tool_registry_rejects_unknown_tools() -> None:
    registry = ToolRegistry()

    with pytest.raises(ToolRegistryError, match="Unknown tool"):
        registry.get("missing")


def test_tool_registry_lists_tool_names() -> None:
    registry = ToolRegistry()
    registry.register(FakeTool(name="second"))
    registry.register(FakeTool(name="first"))

    assert registry.list_names() == ("first", "second")
