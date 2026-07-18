"""Conversation metadata domain models."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ConversationMetadata:
    """Metadata captured during conversation extraction."""

    source_url: str
    final_url: str
    title: str
    raw_html: str
    fetch_time_ms: int
    extra: dict[str, Any] = field(default_factory=dict)
