"""Base importer abstractions."""

from abc import ABC, abstractmethod
from urllib.parse import urlparse

from app.domain.enums import Platform


class BaseImporter(ABC):
    """Base class for platform importers."""

    platform: Platform

    @abstractmethod
    def detect(self, url: str) -> bool:
        """Return whether this importer supports the supplied URL."""

    def fetch(self, url: str) -> None:
        """Fetch a conversation from the supplied URL."""
        raise NotImplementedError

    @staticmethod
    def _host_matches(url: str, allowed_hosts: set[str]) -> bool:
        """Return whether the URL host matches an allowed host or subdomain."""
        hostname = urlparse(url).hostname
        if hostname is None:
            return False

        normalized_host = hostname.lower()
        return any(
            normalized_host == host or normalized_host.endswith(f".{host}")
            for host in allowed_hosts
        )
