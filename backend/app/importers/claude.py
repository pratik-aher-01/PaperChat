"""Claude URL importer detection."""

from app.domain.enums import Platform
from app.importers.base import BaseImporter


class ClaudeImporter(BaseImporter):
    """Importer selector for Claude URLs."""

    platform = Platform.CLAUDE
    allowed_hosts = {"claude.ai"}

    def detect(self, url: str) -> bool:
        """Return whether the URL belongs to Claude."""
        return self._host_matches(url, self.allowed_hosts)
