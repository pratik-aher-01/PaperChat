"""Tests for PaperChat v2 Conversation Compiler pipeline."""

from app.domain.conversation import Conversation
from app.domain.enums import ConversationCategory, ExportProfile, Platform
from app.domain.message import Message
from app.domain.metadata import ConversationMetadata
from app.services.compiler import ConversationCompiler


def test_compiler_compiles_learning_conversation_to_sdm() -> None:
    """Compile a learning conversation into a structured SemanticDocument."""
    messages = (
        Message(id="u1", role="user", plain_text="Teach me Data Science"),
        Message(id="a1", role="assistant", plain_text="# Topic 1: Types of Data\nStructured and Unstructured data."),
    )
    conv = Conversation(
        platform=Platform.GEMINI,
        title="Data Science Lesson",
        messages=messages,
        metadata=ConversationMetadata(
            source_url="https://gemini.google.com/share/test",
            final_url="https://gemini.google.com/share/test",
            title="Data Science Lesson",
            raw_html="",
            fetch_time_ms=100,
        ),
        raw_html="",
    )

    compiler = ConversationCompiler()
    doc = compiler.compile(conv)

    assert doc.metadata.title == "Data Science Lesson"
    assert doc.metadata.category == ConversationCategory.LEARNING
    assert doc.metadata.profile == ExportProfile.STUDY_NOTES
    assert doc.theme == "academic"
    assert len(doc.sections) >= 1
    assert any("Topic 1: Types of Data" in s.title for s in doc.sections)
