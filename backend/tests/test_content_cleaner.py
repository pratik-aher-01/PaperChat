"""Tests for PaperChat v2 Content Cleaner."""

from app.services.cleaner.content_cleaner import ContentCleaner


def test_cleaner_strips_filler_phrases() -> None:
    """Ensure conversational fluff phrases are removed."""
    cleaner = ContentCleaner()
    raw = "Sure! I'd be happy to help you with that. Spot on! You nailed both questions. Here is the answer."
    cleaned = cleaner.clean_text(raw, strip_fluff=True)

    assert "Sure! I'd be happy to help" not in cleaned
    assert "Spot on!" not in cleaned
    assert "You nailed both questions" not in cleaned
    assert "Here is the answer." in cleaned


def test_cleaner_deduplicates_code_blocks() -> None:
    """Ensure duplicate code blocks are removed."""
    cleaner = ContentCleaner()
    code_block = "```python\nprint('hello')\n```"
    raw = f"First section:\n{code_block}\n\nRepeated section:\n{code_block}"
    cleaned = cleaner.deduplicate_code_blocks(raw)

    assert cleaned.count("print('hello')") == 1
