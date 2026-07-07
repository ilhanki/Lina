from lina.tools.tool import ToolResult


def test_tool_result_stores_text() -> None:
    result = ToolResult(text="Done")

    assert result.text == "Done"
