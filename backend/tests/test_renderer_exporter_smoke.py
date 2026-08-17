"""Smoke checks for document rendering and PDF export."""

import asyncio

import pytest

from app.api.exporter import export_pdf, generate_pdf, get_pdf_exporter
from app.api.importer import (
    get_browser_fetcher,
    get_conversation_normalizer,
    get_importer_factory,
    get_parser_factory,
)
from app.domain.conversation import Conversation
from app.domain.enums import Platform
from app.domain.message import Message
from app.domain.metadata import ConversationMetadata
from app.exporters.pdf import PdfExporter
from app.importers.factory import ImporterFactory
from app.importers.registry import create_default_registry
from app.main import create_app
from app.parsers.factory import ParserFactory
from app.parsers.registry import create_default_parser_registry
from app.renderer.html_renderer import HtmlRenderer
from app.services.conversation_normalizer import ConversationNormalizer
from fastapi.testclient import TestClient


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
    assert '<ol class="toc-list">' in html
    assert 'href="#u1"' in html
    assert '<figure class="code-block language-python">' in html
    assert '<code class="highlight">' in html
    assert "<table>" in html
    assert 'class="page-break"' in html
    assert 'style="' not in html


def test_toc_contains_one_entry_per_heading() -> None:
    """TOC contains anchors for each rendered prompt."""
    conversation = build_conversation()
    html = HtmlRenderer().render(conversation)

    assert html.count('href="#u1"') == 1
    assert '<span class="toc-title">Explain tables and code.</span>' in html
    assert '<span class="toc-leader"></span>' in html
    assert '<span class="toc-page" aria-hidden="true"></span>' in html


def test_html_renderer_applies_custom_settings() -> None:
    """Renderer applies custom typography, font size, theme, and cover options."""
    conversation = build_conversation()
    html = HtmlRenderer(
        layout="two-column",
        font_family="serif",
        font_size="large",
        line_spacing="relaxed",
        theme="dark",
        show_cover=False,
    ).render(conversation)

    assert "layout-two-column font-serif size-large spacing-relaxed theme-dark no-cover" in html


def test_known_language_code_block_uses_pygments_spans() -> None:
    """Known language fences are syntax highlighted when Pygments is available."""
    pytest.importorskip("pygments")

    html = HtmlRenderer().render(build_conversation())

    assert '<span class="nb">print</span>' in html or '<span class="k">print</span>' in html


def test_unknown_language_code_block_does_not_raise() -> None:
    """Unknown language names fall back to plain text."""
    conversation = build_conversation()
    message = Message(
        id="a2",
        role="assistant",
        plain_text="```unknown-garbage-language\nhello\n```",
    )
    conversation = Conversation(
        platform=conversation.platform,
        title=conversation.title,
        messages=(message,),
        metadata=conversation.metadata,
        raw_html=conversation.raw_html,
    )

    html = HtmlRenderer().render(conversation)

    assert "unknown-garbage-language" in html
    assert "hello" in html


def test_missing_language_code_block_does_not_raise() -> None:
    """Missing language labels fall back to text highlighting."""
    conversation = build_conversation()
    message = Message(id="a2", role="assistant", plain_text="```\nhello\n```")
    conversation = Conversation(
        platform=conversation.platform,
        title=conversation.title,
        messages=(message,),
        metadata=conversation.metadata,
        raw_html=conversation.raw_html,
    )

    html = HtmlRenderer().render(conversation)

    assert "<figcaption>code</figcaption>" in html
    assert "hello" in html


async def test_pdf_exporter_outputs_pdf_bytes() -> None:
    """PDF exporter produces a PDF byte stream."""
    pytest.importorskip("playwright")
    html = HtmlRenderer().render(build_conversation())
    pdf = await PdfExporter().export(html)

    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 1_000


class FakePdfExporter:
    """Test PDF exporter that avoids browser dependencies."""

    async def export(self, html: str, **kwargs) -> bytes:
        """Return deterministic PDF-like bytes."""
        assert "<!doctype html>" in html
        return b"%PDF-1.4\n% fake\n"


class FakeFetcher:
    """Test fetcher for one-call generation."""

    async def fetch(self, url: str):
        """Return deterministic ChatGPT-like HTML."""
        from app.domain.fetch_result import FetchResult
        html = """
        <html>
          <head><title>Generated Fixture</title></head>
          <body>
            <div data-message-author-role="user" data-message-id="u1">
              <div class="whitespace-pre-wrap">Hello</div>
            </div>
            <div data-message-author-role="assistant" data-message-id="a1">
              <div class="markdown"><h2>Answer</h2><p>Hi there</p></div>
            </div>
          </body>
        </html>
        """
        return FetchResult(
            url=url,
            final_url=url,
            title="Generated Fixture",
            html=html,
            status=200,
            fetch_time_ms=1,
        )


def test_export_pdf_api_returns_pdf_bytes() -> None:
    """The export endpoint keeps its public response contract."""
    app = create_app()
    app.dependency_overrides[get_pdf_exporter] = lambda: FakePdfExporter()
    client = TestClient(app)

    response = client.post("/api/export/pdf", json=_conversation_payload())

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")


def test_generate_api_returns_pdf_bytes() -> None:
    """The one-call generation endpoint keeps its public response contract."""
    app = create_app()
    app.dependency_overrides[get_pdf_exporter] = lambda: FakePdfExporter()
    app.dependency_overrides[get_importer_factory] = lambda: ImporterFactory(create_default_registry())
    app.dependency_overrides[get_browser_fetcher] = lambda: FakeFetcher()
    app.dependency_overrides[get_parser_factory] = lambda: ParserFactory(create_default_parser_registry())
    app.dependency_overrides[get_conversation_normalizer] = lambda: ConversationNormalizer()
    client = TestClient(app)

    response = client.post("/api/generate", json={"url": "https://chatgpt.com/c/example"})

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")


def _conversation_payload() -> dict[str, object]:
    """Build an API-compatible conversation payload."""
    conversation = build_conversation()
    return {
        "platform": conversation.platform.value,
        "title": conversation.title,
        "messages": [
            {
                "id": message.id,
                "role": message.role,
                "plain_text": message.plain_text,
                "content_blocks": [],
            }
            for message in conversation.messages
        ],
        "metadata": {
            "source_url": conversation.metadata.source_url,
            "final_url": conversation.metadata.final_url,
            "title": conversation.metadata.title,
            "raw_html": conversation.metadata.raw_html,
            "fetch_time_ms": conversation.metadata.fetch_time_ms,
            "extra": {},
        },
    }


def test_qr_generator_creates_valid_data_uri() -> None:
    """QR code generator creates a base64-encoded PNG Data URI for valid URLs."""
    from app.renderer.qr_generator import generate_qr_data_uri

    data_uri = generate_qr_data_uri("https://chatgpt.com/share/6a54d9ee-0454-4638")
    assert data_uri.startswith("data:image/png;base64,")
    assert len(data_uri) > 100

    empty_uri = generate_qr_data_uri("")
    assert empty_uri == ""


def test_html_renderer_embeds_qr_code_and_open_link_on_cover() -> None:
    """HTML renderer embeds base64 QR code image and clickable original chat link on the cover."""
    conversation = build_conversation()
    html = HtmlRenderer().render(conversation)

    assert "data:image/png;base64," in html
    assert "Open Original Chat ↗" in html
    assert 'href="https://chatgpt.com/c/example"' in html


def test_semantic_document_renderer_elements_and_callouts() -> None:
    """Verify SemanticDocument renders CALLOUT, QUIZ, TAKEAWAYS, and code blocks correctly."""
    from app.domain.enums import ConversationCategory, ExportProfile
    from app.domain.semantic_document import (
        DocumentElement,
        DocumentMetadata,
        DocumentSection,
        ElementKind,
        SemanticDocument,
    )

    doc = SemanticDocument(
        metadata=DocumentMetadata(
            title="Advanced ML Guide",
            subtitle="Deep Learning Study Notes",
            category=ConversationCategory.LEARNING,
            profile=ExportProfile.STUDY_NOTES,
            platform=Platform.CHATGPT,
            source_url="https://chatgpt.com/share/ml",
            total_sections=1,
        ),
        sections=[
            DocumentSection(
                id="sec-01",
                title="Supervised vs Unsupervised",
                kicker="Chapter 01",
                elements=[
                    DocumentElement(
                        kind=ElementKind.CALLOUT,
                        content="What is the difference between supervised and unsupervised learning?",
                        metadata={"label": "User Query"},
                    ),
                    DocumentElement(
                        kind=ElementKind.PARAGRAPH,
                        content="### Key Distinctions\nSupervised uses labeled datasets.",
                    ),
                    DocumentElement(
                        kind=ElementKind.QUIZ_ITEM,
                        content="What is an example of unsupervised clustering?",
                    ),
                    DocumentElement(
                        kind=ElementKind.KEY_TAKEAWAYS,
                        content="Supervised predicts, unsupervised discovers patterns.",
                    ),
                ],
            )
        ],
    )

    html = HtmlRenderer().render_semantic_document(doc)

    assert '<div class="callout callout-prompt">' in html
    assert '<span class="callout-badge">User Query</span>' in html
    assert "Supervised vs Unsupervised" in html
    assert '<div class="quiz-box">' in html
    assert '<blockquote class="key-takeaways">' in html


if __name__ == "__main__":
    test_html_renderer_outputs_document()
    test_qr_generator_creates_valid_data_uri()
    test_html_renderer_embeds_qr_code_and_open_link_on_cover()
    asyncio.run(test_pdf_exporter_outputs_pdf_bytes())