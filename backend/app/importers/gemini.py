"""Gemini URL importer detection."""

from app.domain.enums import Platform
from app.importers.base import BaseImporter


class GeminiImporter(BaseImporter):
    """Importer selector for Gemini URLs."""

    platform = Platform.GEMINI
    allowed_hosts = {"gemini.google.com", "share.gemini.google", "bard.google.com"}

    def detect(self, url: str) -> bool:
        """Return whether the URL belongs to Gemini."""
        return self._host_matches(url, self.allowed_hosts)
