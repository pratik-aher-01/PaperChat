"""Unit tests for RawTextParser (paste-text conversation parsing)."""

import pytest
from app.domain.enums import Platform
from app.parsers.raw_text import RawTextParser
from exceptions import ParserException


def test_raw_text_parser_labeled_dialogue() -> None:
    """Parses transcripts with explicit User: / Assistant: role headers."""
    sample = """
User: What is gradient descent in machine learning?

Assistant: Gradient descent is an optimization algorithm used to minimize a loss function by iteratively moving in the direction of steepest descent.

User: What is learning rate?

Assistant: The learning rate is a hyperparameter that controls the step size taken towards the minimum at each iteration.
"""
    parser = RawTextParser()
    conv = parser.parse(sample)

    assert conv.platform == Platform.CUSTOM
    assert len(conv.messages) == 4
    assert conv.messages[0].role == "user"
    assert "gradient descent" in conv.messages[0].plain_text.lower()
    assert conv.messages[1].role == "assistant"
    assert conv.messages[2].role == "user"
    assert conv.messages[3].role == "assistant"


def test_raw_text_parser_heading_dialogue() -> None:
    """Parses markdown heading dialogues (# Question / answer)."""
    sample = """
# What is a HashMap?
A HashMap is an associative array that maps keys to values using a hashing function for O(1) average lookup.

# What is collision resolution?
Common strategies include separate chaining and open addressing (linear probing).
"""
    parser = RawTextParser()
    conv = parser.parse(sample)

    assert len(conv.messages) == 4
    assert conv.messages[0].role == "user"
    assert conv.messages[1].role == "assistant"


def test_raw_text_parser_alternating_paragraphs() -> None:
    """Parses unlabelled alternating text blocks."""
    sample = """
Explain quantum computing simply.

Quantum computing leverages quantum mechanics principles like superposition and entanglement to solve complex problems exponentially faster.
"""
    parser = RawTextParser()
    conv = parser.parse(sample)

    assert len(conv.messages) == 2
    assert conv.messages[0].role == "user"
    assert conv.messages[1].role == "assistant"


def test_raw_text_parser_rejects_empty_string() -> None:
    """Rejects empty or whitespace-only input."""
    parser = RawTextParser()
    with pytest.raises(ParserException):
        parser.parse("   ")
