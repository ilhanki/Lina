from datetime import datetime

from lina.tools.builtin import CurrentTimeTool, EchoTool
from lina.tools.permissions import PermissionLevel
from lina.tools.tool import ToolResult


def test_echo_tool_is_safe() -> None:
    tool = EchoTool()

    assert tool.name == "echo"
    assert tool.permission_level is PermissionLevel.SAFE


def test_echo_tool_returns_input_text() -> None:
    tool = EchoTool()

    result = tool.execute("Hello")

    assert result == ToolResult(text="Hello")


def test_current_time_tool_is_safe() -> None:
    tool = CurrentTimeTool()

    assert tool.name == "current_time"
    assert tool.permission_level is PermissionLevel.SAFE


def test_current_time_tool_returns_local_time() -> None:
    tool = CurrentTimeTool(clock=lambda: datetime(2026, 7, 7, 15, 42))

    result = tool.execute()

    assert result == ToolResult(text="Şu an saat 15:42.")
