"""Claude conversation parser."""

from app.domain.conversation import Conversation
from app.domain.enums import Platform
from app.domain.fetch_result import FetchResult
from app.parsers.base import BaseParser


class ClaudeParser(BaseParser):
    """Parser placeholder for Claude conversations."""

    platform = Platform.CLAUDE

    def parse(self, fetch_result: FetchResult) -> Conversation:
        """Parse a Claude document into a conversation."""
        raise NotImplementedError("Claude conversation extraction is not implemented yet.")
