from dataclasses import dataclass

import pytest

from lina.services.tool_execution_service import (
    ToolExecutionError,
    ToolExecutionService,
)
from lina.tools.permissions import PermissionLevel
from lina.tools.registry import ToolRegistry
from lina.tools.tool import ToolResult


@dataclass(frozen=True)
class FakeTool:
    name: str
    permission_level: PermissionLevel
    description: str = "Fake tool"

    def execute(self, input_text: str = "") -> ToolResult:
        return ToolResult(text=f"Executed: {input_text}")


def test_tool_execution_service_executes_safe_tool() -> None:
    registry = ToolRegistry()
    registry.register(FakeTool(name="safe", permission_level=PermissionLevel.SAFE))
    service = ToolExecutionService(tool_registry=registry)

    result = service.execute("safe", "Hello")

    assert result == ToolResult(text="Executed: Hello")


def test_tool_execution_service_rejects_non_safe_tool() -> None:
    registry = ToolRegistry()
    registry.register(
        FakeTool(name="dangerous", permission_level=PermissionLevel.DANGEROUS)
    )
    service = ToolExecutionService(tool_registry=registry)

    with pytest.raises(ToolExecutionError, match="cannot be executed automatically"):
        service.execute("dangerous")


def test_tool_execution_service_wraps_unknown_tool_errors() -> None:
    registry = ToolRegistry()
    service = ToolExecutionService(tool_registry=registry)

    with pytest.raises(ToolExecutionError, match="Tool is not available"):
        service.execute("missing")


def test_tool_execution_service_does_not_wrap_tool_exceptions() -> None:
    @dataclass(frozen=True)
    class FailingTool:
        name: str = "failing"
        permission_level: PermissionLevel = PermissionLevel.SAFE
        description: str = "Failing tool"

        def execute(self, input_text: str = "") -> ToolResult:
            raise ValueError("Tool execution failed internally")

    registry = ToolRegistry()
    registry.register(FailingTool())
    service = ToolExecutionService(tool_registry=registry)

    with pytest.raises(ValueError, match="Tool execution failed internally"):
        service.execute("failing")
