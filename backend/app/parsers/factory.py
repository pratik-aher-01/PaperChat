"""Parser factory."""

from app.domain.enums import Platform
from app.parsers.base import BaseParser
from app.parsers.registry import ParserRegistry


class ParserFactory:
    """Select parsers for platforms."""

    def __init__(self, registry: ParserRegistry) -> None:
        """Initialize the factory."""
        self._registry = registry

    def get_parser(self, platform: Platform) -> BaseParser | None:
        """Return a parser for the supplied platform."""
        return self._registry.get(platform)
