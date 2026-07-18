"""Smoke checks for document rendering and PDF export."""

import asyncio

from app.domain.conversation import Conversation
from app.domain.enums import Platform
from app.domain.message import Message
from app.domain.metadata import ConversationMetadata
from app.exporters.pdf import PdfExporter
from app.renderer.html_renderer import HtmlRenderer


def build_conversation() -> Conversation:
    """Create a deterministic conversation fixture."""
    metadata = ConversationMetadata(
        source_url="https://chatgpt.com/c/example",
        final_url="https://chatgpt.com/c/example",
        title="Renderer Fixture",
        raw_html="<html></html>",
        fetch_time_ms=10,
    )
    messages = (
        Message(id="u1", role="user", plain_text="Explain tables and code."),
        Message(
            id="a1",
            role="assistant",
            plain_text=(
                "## Technical Notes\n\n"
                "Use `inline_code` carefully.\n\n"
                "- First\n"
                "  - Nested\n\n"
                "```python\n"
                "print(\"hello\")\n"
                "```\n\n"
                "| Feature | Status |\n"
                "| --- | --- |\n"
                "| Tables | Supported |\n\n"
                "> Study note\n\n"
                "[[PAGE_BREAK]]\n\n"
                "After the break."
            ),
        ),
    )
    return Conversation(
        platform=Platform.CHATGPT,
        title="Renderer Fixture",
        messages=messages,
        metadata=metadata,
        raw_html="<html></html>",
    )


def test_html_renderer_outputs_document() -> None:
    """Renderer produces a complete semantic HTML document."""
    html = HtmlRenderer().render(build_conversation())

    assert "<!doctype html>" in html
    assert "Technical Notes" in html
    assert '<nav class="toc"' in html
    assert '<figure class="code-block language-python">' in html
    assert "<table>" in html
    assert 'class="page-break"' in html
    assert 'style="' not in html


async def test_pdf_exporter_outputs_pdf_bytes() -> None:
    """PDF exporter produces a PDF byte stream."""
    html = HtmlRenderer().render(build_conversation())
    pdf = await PdfExporter().export(html)

    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1_000


if __name__ == "__main__":
    test_html_renderer_outputs_document()
    asyncio.run(test_pdf_exporter_outputs_pdf_bytes())
