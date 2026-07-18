"""Conversation content block domain models."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ContentBlock:
    """A normalized unit of message content."""

    type: str
    text: str
