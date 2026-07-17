"""Safe, deliberately small rich-text renderer for assistant messages."""

from __future__ import annotations

from html import escape
import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel


_BOLD = re.compile(r"\*\*(.+?)\*\*")
_INLINE_CODE = re.compile(r"`([^`\n]+)`")


def render_safe_markdown(text: str) -> str:
    """Render a conservative Markdown subset after escaping all model HTML."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    output: list[str] = []
    paragraph: list[str] = []
    list_kind: str | None = None
    code_lines: list[str] = []
    in_code = False

    def flush_paragraph() -> None:
        if paragraph:
            output.append(f"<p>{'<br>'.join(_inline(item) for item in paragraph)}</p>")
            paragraph.clear()

    def close_list() -> None:
        nonlocal list_kind
        if list_kind is not None:
            output.append(f"</{list_kind}>")
            list_kind = None

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_paragraph()
            close_list()
            if in_code:
                output.append(f"<pre><code>{escape(chr(10).join(code_lines))}</code></pre>")
                code_lines.clear()
            in_code = not in_code
            continue
        if in_code:
            code_lines.append(line)
            continue
        if not stripped:
            flush_paragraph()
            close_list()
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            close_list()
            level = len(heading.group(1)) + 2
            output.append(f"<h{level}>{_inline(heading.group(2))}</h{level}>")
            continue
        unordered = re.match(r"^[-*]\s+(.+)$", stripped)
        ordered = re.match(r"^\d+[.)]\s+(.+)$", stripped)
        if unordered or ordered:
            flush_paragraph()
            desired = "ul" if unordered else "ol"
            if list_kind != desired:
                close_list()
                output.append(f"<{desired}>")
                list_kind = desired
            match = unordered or ordered
            output.append(f"<li>{_inline(match.group(1))}</li>")
            continue
        close_list()
        paragraph.append(stripped)

    if in_code:
        output.append(f"<pre><code>{escape(chr(10).join(code_lines))}</code></pre>")
    flush_paragraph()
    close_list()
    return "".join(output) or "<p></p>"


def _inline(text: str) -> str:
    escaped = escape(text)
    code_parts: list[str] = []

    def hold_code(match: re.Match[str]) -> str:
        code_parts.append(f"<code>{match.group(1)}</code>")
        return f"\x00CODE{len(code_parts) - 1}\x00"

    escaped = _INLINE_CODE.sub(hold_code, escaped)
    escaped = _BOLD.sub(r"<strong>\1</strong>", escaped)
    for index, value in enumerate(code_parts):
        escaped = escaped.replace(f"\x00CODE{index}\x00", value)
    return escaped


class RichMessageLabel(QLabel):
    """A QLabel that renders rich content while retaining exact plain text."""

    def __init__(self, text: str, parent=None) -> None:
        super().__init__(parent)
        self._plain_text = ""
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setOpenExternalLinks(False)
        self.setText(text)

    def setText(self, text: str) -> None:  # noqa: N802 - Qt API compatibility
        self._plain_text = text
        super().setText(render_safe_markdown(text))

    def text(self) -> str:
        return self._plain_text
