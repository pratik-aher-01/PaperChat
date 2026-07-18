"""Base acquisition interfaces."""

from abc import ABC, abstractmethod

from app.domain.fetch_result import FetchResult


class BaseFetcher(ABC):
    """Base interface for URL acquisition."""

    @abstractmethod
    async def fetch(self, url: str) -> FetchResult:
        """Fetch a URL and return the acquisition result."""
