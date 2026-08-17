"""Smoke checks for the Gemini parser."""

from app.domain.fetch_result import FetchResult
from app.parsers.gemini import GeminiParser
from app.services.conversation_normalizer import ConversationNormalizer


def test_gemini_parser_extracts_messages_and_markdown() -> None:
    """Parse Gemini HTML DOM structure into a normalized conversation."""
    html = """
    <html>
      <head><title>Gemini Quantum Physics Chat - Gemini</title></head>
      <body>
        <div class="user-query" data-id="u1">
          <div class="query-text">What is quantum entanglement?</div>
        </div>
        <div class="model-response" data-id="m1">
          <div class="message-content">
            <h2>Quantum Entanglement</h2>
            <p>Quantum entanglement occurs when pairs of particles interact.</p>
            <pre><code class="language-python">def entangle(a, b): return True</code></pre>
          </div>
        </div>
      </body>
    </html>
    """
    fetch_result = FetchResult(
        url="https://gemini.google.com/share/test",
        final_url="https://gemini.google.com/share/test",
        title="Gemini Quantum Physics Chat",
        html=html,
        status=200,
        fetch_time_ms=1,
    )

    conversation = ConversationNormalizer().normalize(GeminiParser().parse(fetch_result))

    assert conversation.title == "Gemini Quantum Physics Chat"
    assert len(conversation.messages) == 2
    assert [m.role for m in conversation.messages] == ["user", "assistant"]
    assert conversation.messages[0].plain_text == "What is quantum entanglement?"
    assert "## Quantum Entanglement" in conversation.messages[1].plain_text
    assert '```python\ndef entangle(a, b): return True\n```' in conversation.messages[1].plain_text


def test_gemini_parser_extracts_embedded_script_data() -> None:
    """Parse embedded JSON payloads when DOM elements are virtualized."""
    html = """
    <html>
      <head><title>Gemini Embedded</title></head>
      <body>
        <script>
          window.WIZ_global_data = {
            "payload": {
              "message1": {"role": "user", "text": "Hello Gemini"},
              "message2": {"role": "model", "text": "Hello! How can I help?"}
            }
          };
        </script>
      </body>
    </html>
    """
    fetch_result = FetchResult(
        url="https://gemini.google.com/share/test",
        final_url="https://gemini.google.com/share/test",
        title="Gemini Embedded",
        html=html,
        status=200,
        fetch_time_ms=1,
    )

    conversation = GeminiParser().parse(fetch_result)
    assert len(conversation.messages) == 2
    assert [m.role for m in conversation.messages] == ["user", "assistant"]
    assert conversation.messages[0].plain_text == "Hello Gemini"
    assert conversation.messages[1].plain_text == "Hello! How can I help?"
