"""Fetch result domain model."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FetchResult:
    """Rendered document fetched from a shared conversation URL."""

    url: str
    final_url: str
    title: str
    html: str
    status: int | None
    fetch_time_ms: int
    metadata: dict[str, Any] = field(default_factory=dict)
