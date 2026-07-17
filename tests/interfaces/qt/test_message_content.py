from lina.interfaces.qt.message_content import RichMessageLabel, render_safe_markdown
from PySide6.QtWidgets import QLabel


def test_safe_markdown_renders_structure_and_escapes_model_html() -> None:
    rendered = render_safe_markdown(
        "## Başlık\n\n- **Güçlü**\n- `kod`\n\n<script>alert(1)</script>"
    )

    assert "<h4>Başlık</h4>" in rendered
    assert "<ul>" in rendered
    assert "<strong>Güçlü</strong>" in rendered
    assert "<code>kod</code>" in rendered
    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered


def test_rich_label_preserves_exact_plain_text(qtbot) -> None:
    label = RichMessageLabel("**Merhaba**")
    qtbot.addWidget(label)

    assert label.text() == "**Merhaba**"
    assert "<strong>Merhaba</strong>" in QLabel.text(label)
    label.setText("Yeni `kod`")
    assert label.text() == "Yeni `kod`"
