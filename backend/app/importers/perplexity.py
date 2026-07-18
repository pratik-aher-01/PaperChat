"""Perplexity URL importer detection."""

from app.domain.enums import Platform
from app.importers.base import BaseImporter


class PerplexityImporter(BaseImporter):
    """Importer selector for Perplexity URLs."""

    platform = Platform.PERPLEXITY
    allowed_hosts = {"perplexity.ai"}

    def detect(self, url: str) -> bool:
        """Return whether the URL belongs to Perplexity."""
        return self._host_matches(url, self.allowed_hosts)
