"""Fetcher factory."""

from app.acquisition.base import BaseFetcher
from app.acquisition.browser import BrowserFetcher


class FetcherFactory:
    """Create acquisition fetchers."""

    def create_browser_fetcher(self) -> BaseFetcher:
        """Create the default rendered-page fetcher."""
        return BrowserFetcher()
