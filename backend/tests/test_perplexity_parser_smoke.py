"""Smoke checks for the Perplexity parser."""

from app.domain.fetch_result import FetchResult
from app.parsers.perplexity import PerplexityParser
from app.services.conversation_normalizer import ConversationNormalizer


def test_perplexity_parser_extracts_query_and_answer() -> None:
    """Parse Perplexity search page into user query and assistant response."""
    html = """
    <html>
      <head><title>Perplexity Search - Perplexity</title></head>
      <body>
        <div data-testid="user-query" class="query-text">
          <h1>How does web scraping work?</h1>
        </div>
        <div data-testid="answer" class="ds-markdown">
          <p>Web scraping automates extracting data from websites.</p>
          <h2>Key Steps</h2>
          <ul>
            <li>Fetch HTML</li>
            <li>Parse DOM</li>
          </ul>
        </div>
      </body>
    </html>
    """
    fetch_result = FetchResult(
        url="https://perplexity.ai/search/test",
        final_url="https://perplexity.ai/search/test",
        title="Perplexity Search",
        html=html,
        status=200,
        fetch_time_ms=1,
    )

    conversation = ConversationNormalizer().normalize(PerplexityParser().parse(fetch_result))

    assert conversation.title == "How does web scraping work?"
    assert len(conversation.messages) == 2
    assert [m.role for m in conversation.messages] == ["user", "assistant"]
    assert "How does web scraping work?" in conversation.messages[0].plain_text
    assert "Web scraping automates extracting data from websites." in conversation.messages[1].plain_text
    assert "## Key Steps" in conversation.messages[1].plain_text


def test_perplexity_parser_fallback_heading_and_markdown() -> None:
    """Fallback extraction when specific attributes are absent."""
    html = """
    <html>
      <head><title>Fallback Title</title></head>
      <body>
        <h1>What is machine learning?</h1>
        <article class="ds-markdown">
          <p>Machine learning is a field of artificial intelligence.</p>
        </article>
      </body>
    </html>
    """
    fetch_result = FetchResult(
        url="https://perplexity.ai/search/test2",
        final_url="https://perplexity.ai/search/test2",
        title="Fallback Title",
        html=html,
        status=200,
        fetch_time_ms=1,
    )

    conversation = PerplexityParser().parse(fetch_result)
    assert len(conversation.messages) == 2
    assert conversation.messages[0].plain_text == "What is machine learning?"
    assert "Machine learning is a field of artificial intelligence." in conversation.messages[1].plain_text
