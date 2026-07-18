"""Gemini conversation parser."""

from app.domain.conversation import Conversation
from app.domain.enums import Platform
from app.domain.fetch_result import FetchResult
from app.parsers.base import BaseParser


class GeminiParser(BaseParser):
    """Parser placeholder for Gemini conversations."""

    platform = Platform.GEMINI

    def parse(self, fetch_result: FetchResult) -> Conversation:
        """Parse a Gemini document into a conversation."""
        raise NotImplementedError("Gemini conversation extraction is not implemented yet.")
