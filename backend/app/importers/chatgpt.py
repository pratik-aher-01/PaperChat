"""ChatGPT URL importer detection."""

from app.domain.enums import Platform
from app.importers.base import BaseImporter


class ChatGPTImporter(BaseImporter):
    """Importer selector for ChatGPT URLs."""

    platform = Platform.CHATGPT
    allowed_hosts = {"chatgpt.com", "chat.openai.com"}

    def detect(self, url: str) -> bool:
        """Return whether the URL belongs to ChatGPT."""
        return self._host_matches(url, self.allowed_hosts)
