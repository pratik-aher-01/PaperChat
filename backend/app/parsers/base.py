"""Base parser abstractions."""

from abc import ABC, abstractmethod

from app.domain.conversation import Conversation
from app.domain.enums import Platform
from app.domain.fetch_result import FetchResult


class BaseParser(ABC):
    """Base interface for platform conversation parsers."""

    platform: Platform

    @abstractmethod
    def parse(self, fetch_result: FetchResult) -> Conversation:
        """Parse a fetched document into a conversation."""
