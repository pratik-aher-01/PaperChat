"""Base renderer abstractions."""

from abc import ABC, abstractmethod

from app.domain.conversation import Conversation


class BaseRenderer(ABC):
    """Base interface for document renderers."""

    @abstractmethod
    def render(self, conversation: Conversation) -> str:
        """Render a conversation to a document string."""
