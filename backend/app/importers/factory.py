"""Importer factory."""

from app.importers.base import BaseImporter
from app.importers.registry import ImporterRegistry


class ImporterFactory:
    """Select importer instances for supported URLs."""

    def __init__(self, registry: ImporterRegistry) -> None:
        """Initialize the factory with an importer registry."""
        self._registry = registry

    def get_importer(self, url: str) -> BaseImporter | None:
        """Return the first importer that supports the supplied URL."""
        for importer in self._registry.get_importers():
            if importer.detect(url):
                return importer
        return None
