"""Conversation domain models."""

from dataclasses import dataclass, field

from app.domain.enums import Platform
from app.domain.message import Message
from app.domain.metadata import ConversationMetadata


@dataclass(frozen=True)
class ConversationSource:
    """Reference to a conversation source before import processing."""

    url: str
    platform: Platform


@dataclass(frozen=True)
class Conversation:
    """A normalized imported conversation."""

    platform: Platform
    title: str
    messages: tuple[Message, ...]
    metadata: ConversationMetadata
    raw_html: str = field(repr=False)
