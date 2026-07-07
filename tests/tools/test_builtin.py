from lina.tools.builtin import EchoTool
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
