"""Conversation message domain models."""

from dataclasses import dataclass, field

from app.domain.content_block import ContentBlock


@dataclass(frozen=True)
class Message:
    """A normalized conversation message."""

    id: str
    role: str
    plain_text: str
    content_blocks: tuple[ContentBlock, ...] = field(default_factory=tuple)
