"""Domain enumerations."""

from enum import StrEnum


class Platform(StrEnum):
    """Supported conversation platforms."""

    UNKNOWN = "unknown"
    CHATGPT = "chatgpt"
    CLAUDE = "claude"
    GEMINI = "gemini"
    PERPLEXITY = "perplexity"
