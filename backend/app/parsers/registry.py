"""Parser registry."""

from collections.abc import Iterable

from app.domain.enums import Platform
from app.parsers.base import BaseParser
from app.parsers.chatgpt import ChatGPTParser
from app.parsers.claude import ClaudeParser
from app.parsers.gemini import GeminiParser
from app.parsers.perplexity import PerplexityParser


class ParserRegistry:
    """Registry of platform parsers."""

    def __init__(self) -> None:
        """Initialize an empty parser registry."""
        self._parsers: dict[Platform, BaseParser] = {}

    def register(self, parser: BaseParser) -> None:
        """Register a parser."""
        self._parsers[parser.platform] = parser

    def get(self, platform: Platform) -> BaseParser | None:
        """Return the parser for a platform."""
        return self._parsers.get(platform)


def create_parser_registry(parsers: Iterable[BaseParser]) -> ParserRegistry:
    """Create a parser registry from parser instances."""
    registry = ParserRegistry()
    for parser in parsers:
        registry.register(parser)
    return registry


def create_default_parser_registry() -> ParserRegistry:
    """Create the default parser registry."""
    return create_parser_registry(
        (
            ChatGPTParser(),
            ClaudeParser(),
            GeminiParser(),
            PerplexityParser(),
        )
    )
