"""PaperChat exception hierarchy."""


class PaperChatException(Exception):
    """Base exception for PaperChat."""


class ConfigurationException(PaperChatException):
    """Raised for configuration errors."""


class ImporterException(PaperChatException):
    """Raised for importer errors."""


class AcquisitionException(PaperChatException):
    """Raised for acquisition errors."""


class ParserException(PaperChatException):
    """Raised for parser errors."""


class RendererException(PaperChatException):
    """Raised for renderer errors."""


class ExporterException(PaperChatException):
    """Raised for exporter errors."""
