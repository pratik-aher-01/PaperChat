"""Smoke checks for the import parse pipeline."""

import asyncio

from fastapi import HTTPException

from app.api.importer import ImportDetectRequest, parse_import_source
from app.domain.fetch_result import FetchResult
from app.importers.factory import ImporterFactory
from app.importers.registry import create_default_registry
from app.parsers.factory import ParserFactory
from app.parsers.registry import create_default_parser_registry
from app.services.conversation_normalizer import ConversationNormalizer


class FakeFetcher:
    """Test fetcher that returns rendered ChatGPT-like HTML."""

    async def fetch(self, url: str) -> FetchResult:
        """Return a deterministic fetch result."""
        html = """
        <html>
          <head><title>Pipeline Fixture</title></head>
          <body>
            <div data-message-author-role="user" data-message-id="u1">
              <div class="whitespace-pre-wrap">Hello</div>
            </div>
            <div data-message-author-role="assistant" data-message-id="a1">
              <div class="markdown"><p>Hi there</p></div>
            </div>
          </body>
        </html>
        """
        return FetchResult(
            url=url,
            final_url=url,
            title="Pipeline Fixture",
            html=html,
            status=200,
            fetch_time_ms=1,
        )


async def test_parse_pipeline_returns_api_shape() -> None:
    """Parse endpoint orchestration returns only safe response fields."""
    response = await parse_import_source(
        payload=ImportDetectRequest(url="https://chatgpt.com/c/example"),
        importer_factory=ImporterFactory(create_default_registry()),
        fetcher=FakeFetcher(),
        parser_factory=ParserFactory(create_default_parser_registry()),
        normalizer=ConversationNormalizer(),
    )

    assert response.platform == "chatgpt"
    assert response.title == "Pipeline Fixture"
    assert response.message_count == 2
    assert [message.role for message in response.messages] == ["user", "assistant"]
    assert not hasattr(response, "raw_html")


async def test_parse_pipeline_rejects_invalid_url() -> None:
    """Unsupported URLs fail gracefully."""
    try:
        await parse_import_source(
            payload=ImportDetectRequest(url="https://example.com/thread"),
            importer_factory=ImporterFactory(create_default_registry()),
            fetcher=FakeFetcher(),
            parser_factory=ParserFactory(create_default_parser_registry()),
            normalizer=ConversationNormalizer(),
        )
    except HTTPException as exc:
        assert exc.status_code == 400
    else:
        raise AssertionError("Expected unsupported URL to raise HTTPException")


if __name__ == "__main__":
    asyncio.run(test_parse_pipeline_returns_api_shape())
    asyncio.run(test_parse_pipeline_rejects_invalid_url())
