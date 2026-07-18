"""Perplexity conversation parser."""

from app.domain.conversation import Conversation
from app.domain.enums import Platform
from app.domain.fetch_result import FetchResult
from app.parsers.base import BaseParser


class PerplexityParser(BaseParser):
    """Parser placeholder for Perplexity conversations."""

    platform = Platform.PERPLEXITY

    def parse(self, fetch_result: FetchResult) -> Conversation:
        """Parse a Perplexity document into a conversation."""
        raise NotImplementedError("Perplexity conversation extraction is not implemented yet.")
