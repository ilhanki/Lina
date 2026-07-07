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
