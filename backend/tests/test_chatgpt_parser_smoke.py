"""Smoke checks for the ChatGPT parser."""

from app.domain.fetch_result import FetchResult
from app.parsers.chatgpt import ChatGPTParser
from app.services.conversation_normalizer import ConversationNormalizer


def test_chatgpt_parser_preserves_markdown_structures() -> None:
    """Parse semantic ChatGPT HTML and preserve markdown structures."""
    html = """
    <html>
      <head><title>Fixture</title></head>
      <body>
        <div data-message-author-role="user" data-message-id="u1">
          <div class="whitespace-pre-wrap">Explain lists</div>
        </div>
        <div data-message-author-role="assistant" data-message-id="a1">
          <div class="markdown">
            <h2>Answer</h2>
            <p>Use <code>items</code>.</p>
            <ul>
              <li>One<ul><li>Nested</li></ul></li>
              <li>Two</li>
            </ul>
            <pre><code class="language-python">print("hi")</code></pre>
            <table>
              <tr><th>A</th><th>B</th></tr>
              <tr><td>1</td><td>2</td></tr>
            </table>
          </div>
        </div>
      </body>
    </html>
    """
    fetch_result = FetchResult(
        url="https://chatgpt.com/c/test",
        final_url="https://chatgpt.com/c/test",
        title="Fixture",
        html=html,
        status=200,
        fetch_time_ms=1,
    )

    conversation = ConversationNormalizer().normalize(ChatGPTParser().parse(fetch_result))

    assert conversation.title == "Fixture"
    assert len(conversation.messages) == 2
    assert [message.role for message in conversation.messages] == ["user", "assistant"]
    assert conversation.messages[0].plain_text == "Explain lists"

    assistant_text = conversation.messages[1].plain_text
    assert "## Answer" in assistant_text
    assert "`items`" in assistant_text
    assert "- One" in assistant_text
    assert "  - Nested" in assistant_text
    assert '```python\nprint("hi")\n```' in assistant_text
    assert "| A | B |" in assistant_text


def test_chatgpt_parser_uses_collected_virtualized_messages() -> None:
    """Parse messages preserved while the browser scrolled a long chat."""
    html = """
    <html>
      <head><title>Long chat</title></head>
      <body>
        <div data-message-author-role="assistant" data-message-id="a2">
          <div class="markdown"><p>Visible final answer</p></div>
        </div>
        <section data-paperchat-collected-messages="true" hidden>
          <div data-message-author-role="user" data-message-id="u1">
            <div class="markdown"><p>Earlier prompt</p></div>
          </div>
          <div data-message-author-role="assistant" data-message-id="a1">
            <div class="markdown"><p>Earlier answer</p></div>
          </div>
          <div data-message-author-role="assistant" data-message-id="a2">
            <div class="markdown"><p>Visible final answer</p></div>
          </div>
        </section>
      </body>
    </html>
    """
    conversation = ChatGPTParser().parse(_fetch_result(html, title="Long chat"))

    assert conversation.title == "Long chat"
    assert [message.id for message in conversation.messages] == ["u1", "a1", "a2"]
    assert conversation.messages[0].plain_text == "Earlier prompt"


def test_chatgpt_parser_prefers_full_embedded_conversation_data() -> None:
    """Parse full ChatGPT JSON data when the mounted DOM is incomplete."""
    html = """
    <html>
      <head><title>Embedded chat</title></head>
      <body>
        <div data-message-author-role="assistant" data-message-id="a2">
          <div class="markdown"><p>Visible final answer</p></div>
        </div>
        <script type="application/json">
          {
            "props": {
              "pageProps": {
                "mapping": {
                  "u1": {
                    "message": {
                      "id": "u1",
                      "create_time": 1,
                      "author": {"role": "user"},
                      "content": {"parts": ["Earlier prompt"]}
                    }
                  },
                  "a1": {
                    "message": {
                      "id": "a1",
                      "create_time": 2,
                      "author": {"role": "assistant"},
                      "content": {"parts": ["Earlier answer"]}
                    }
                  },
                  "a2": {
                    "message": {
                      "id": "a2",
                      "create_time": 3,
                      "author": {"role": "assistant"},
                      "content": {"parts": ["Visible final answer"]}
                    }
                  }
                }
              }
            }
          }
        </script>
      </body>
    </html>
    """
    conversation = ChatGPTParser().parse(_fetch_result(html, title="Embedded chat"))

    assert [message.id for message in conversation.messages] == ["u1", "a1", "a2"]
    assert len(conversation.messages) == 3


def test_chatgpt_parser_extracts_katex_formulas() -> None:
    """Parse KaTeX DOM structures and extract clean LaTeX math formulas."""
    html = """
    <html>
      <head><title>Math Chat</title></head>
      <body>
        <div data-message-author-role="user" data-message-id="u1">
          <div class="markdown"><p>What is Einstein's equation?</p></div>
        </div>
        <div data-message-author-role="assistant" data-message-id="a1">
          <div class="markdown">
            <p>The equation is <span class="katex"><span class="katex-mathml"><annotation encoding="application/x-tex">E = mc^2</annotation></span><span class="katex-html">E=mc2</span></span>.</p>
            <span class="katex-display"><span class="katex"><span class="katex-mathml"><annotation encoding="application/x-tex">\\int_0^\\infty f(x) dx</annotation></span><span class="katex-html">int_0_inf</span></span></span>
          </div>
        </div>
      </body>
    </html>
    """
    conversation = ChatGPTParser().parse(_fetch_result(html, title="Math Chat"))

    assert len(conversation.messages) == 2
    assistant_text = conversation.messages[1].plain_text
    assert "$ E = mc^2 $" in assistant_text
    assert "$$ \\int_0^\\infty f(x) dx $$" in assistant_text
    # Ensure raw visual katex-html strings were omitted
    assert "E=mc2" not in assistant_text
    assert "int_0_inf" not in assistant_text


def _fetch_result(html: str, title: str = "Fixture") -> FetchResult:
    """Build a parser fetch fixture."""
    return FetchResult(
        url="https://chatgpt.com/c/test",
        final_url="https://chatgpt.com/c/test",
        title=title,
        html=html,
        status=200,
        fetch_time_ms=1,
    )


if __name__ == "__main__":
    test_chatgpt_parser_preserves_markdown_structures()
    test_chatgpt_parser_uses_collected_virtualized_messages()
    test_chatgpt_parser_prefers_full_embedded_conversation_data()
    test_chatgpt_parser_extracts_katex_formulas()
