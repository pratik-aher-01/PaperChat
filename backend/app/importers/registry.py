"""Importer registry."""

from collections.abc import Iterable

from app.importers.base import BaseImporter
from app.importers.chatgpt import ChatGPTImporter
from app.importers.claude import ClaudeImporter
from app.importers.gemini import GeminiImporter
from app.importers.perplexity import PerplexityImporter


class ImporterRegistry:
    """Registry of available importers."""

    def __init__(self) -> None:
        """Initialize an empty importer registry."""
        self._importers: list[BaseImporter] = []

    def register(self, importer: BaseImporter) -> None:
        """Register an importer instance."""
        self._importers.append(importer)

    def get_importers(self) -> tuple[BaseImporter, ...]:
        """Return registered importers."""
        return tuple(self._importers)


def create_registry(importers: Iterable[BaseImporter]) -> ImporterRegistry:
    """Create a registry with the supplied importers."""
    registry = ImporterRegistry()
    for importer in importers:
        registry.register(importer)
    return registry


def create_default_registry() -> ImporterRegistry:
    """Create the default registry of supported importers."""
    return create_registry(
        (
            ChatGPTImporter(),
            ClaudeImporter(),
            GeminiImporter(),
            PerplexityImporter(),
        )
    )
