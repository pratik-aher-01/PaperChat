"""Tests for PaperChat v2 Conversation Analyzer and Classifier."""

from app.domain.conversation import Conversation
from app.domain.enums import ConversationCategory, Platform
from app.domain.message import Message
from app.domain.metadata import ConversationMetadata
from app.services.intelligence.analyzer import ConversationAnalyzer
from app.services.intelligence.classifier import ConversationClassifier


def test_classifier_detects_learning_session() -> None:
    """Classify tutoring/learning conversations as LEARNING."""
    messages = (
        Message(id="u1", role="user", plain_text="Teach me Data Science"),
        Message(id="a1", role="assistant", plain_text="# Topic 1: Types of Data\nLet's test your understanding with a quiz."),
    )
    conv = Conversation(
        platform=Platform.CHATGPT,
        title="Data Science Course",
        messages=messages,
        metadata=ConversationMetadata(
            source_url="https://chatgpt.com/share/test",
            final_url="https://chatgpt.com/share/test",
            title="Data Science Course",
            raw_html="",
            fetch_time_ms=100,
        ),
        raw_html="",
    )

    analyzer = ConversationAnalyzer()
    classifier = ConversationClassifier()
    profile = analyzer.analyze(conv)
    category = classifier.classify(profile, title=conv.title)

    assert category == ConversationCategory.LEARNING


def test_classifier_detects_programming_session() -> None:
    """Classify code-heavy conversations as PROGRAMMING."""
    messages = (
        Message(id="u1", role="user", plain_text="Build a REST API in Python"),
        Message(id="a1", role="assistant", plain_text="```python\nimport fastapi\napp = fastapi.FastAPI()\n```"),
        Message(id="a2", role="assistant", plain_text="```python\n@app.get('/')\ndef root(): return {}\n```"),
        Message(id="a3", role="assistant", plain_text="```python\n@app.post('/items')\ndef create(): pass\n```"),
    )
    conv = Conversation(
        platform=Platform.CLAUDE,
        title="FastAPI REST Server",
        messages=messages,
        metadata=ConversationMetadata(
            source_url="https://claude.ai/share/test",
            final_url="https://claude.ai/share/test",
            title="FastAPI REST Server",
            raw_html="",
            fetch_time_ms=100,
        ),
        raw_html="",
    )

    analyzer = ConversationAnalyzer()
    classifier = ConversationClassifier()
    profile = analyzer.analyze(conv)
    category = classifier.classify(profile, title=conv.title)

    assert category in (ConversationCategory.PROGRAMMING, ConversationCategory.DEBUGGING)
