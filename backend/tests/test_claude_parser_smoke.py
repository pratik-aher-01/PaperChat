"""Smoke checks for the Claude parser."""

from app.domain.fetch_result import FetchResult
from app.parsers.claude import ClaudeParser
from app.services.conversation_normalizer import ConversationNormalizer


def test_claude_parser_extracts_messages_and_markdown() -> None:
    """Parse Claude HTML DOM structure into a normalized conversation."""
    html = """
    <html>
      <head><title>Claude Async Python - Claude</title></head>
      <body>
        <div class="font-user-message" data-testid="user-message">
          <div>Explain asyncio event loops.</div>
        </div>
        <div class="font-claude-message" data-testid="assistant-message">
          <div class="grid">
            <h2>Asyncio Event Loop</h2>
            <p>An event loop executes asynchronous tasks.</p>
            <ul>
              <li>Task 1</li>
              <li>Task 2</li>
            </ul>
          </div>
        </div>
      </body>
    </html>
    """
    fetch_result = FetchResult(
        url="https://claude.ai/share/test",
        final_url="https://claude.ai/share/test",
        title="Claude Async Python",
        html=html,
        status=200,
        fetch_time_ms=1,
    )

    conversation = ConversationNormalizer().normalize(ClaudeParser().parse(fetch_result))

    assert conversation.title == "Claude Async Python"
    assert len(conversation.messages) == 2
    assert [m.role for m in conversation.messages] == ["user", "assistant"]
    assert conversation.messages[0].plain_text == "Explain asyncio event loops."
    assert "## Asyncio Event Loop" in conversation.messages[1].plain_text
    assert "- Task 1" in conversation.messages[1].plain_text


def test_claude_parser_extracts_embedded_next_data() -> None:
    """Parse embedded __NEXT_DATA__ JSON script payload."""
    html = """
    <html>
      <head><title>Claude Embedded</title></head>
      <body>
        <script id="__NEXT_DATA__" type="application/json">
          {
            "props": {
              "pageProps": {
                "chat_messages": [
                  {"sender": "human", "text": "What is rust?"},
                  {"sender": "assistant", "text": "Rust is a systems programming language focusing on safety."}
                ]
              }
            }
          }
        </script>
      </body>
    </html>
    """
    fetch_result = FetchResult(
        url="https://claude.ai/share/test",
        final_url="https://claude.ai/share/test",
        title="Claude Embedded",
        html=html,
        status=200,
        fetch_time_ms=1,
    )

    conversation = ClaudeParser().parse(fetch_result)
    assert len(conversation.messages) == 2
    assert [m.role for m in conversation.messages] == ["user", "assistant"]
    assert conversation.messages[0].plain_text == "What is rust?"
    assert conversation.messages[1].plain_text == "Rust is a systems programming language focusing on safety."
