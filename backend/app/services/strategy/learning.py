"""Learning Session document compilation strategy."""

import re

from app.domain.conversation import Conversation
from app.domain.enums import ConversationCategory, ExportProfile
from app.domain.semantic_document import (
    DocumentElement,
    DocumentMetadata,
    DocumentSection,
    ElementKind,
    SemanticDocument,
)
from app.services.intelligence.analyzer import ConversationProfile
from app.services.strategy.base import BaseDocumentStrategy


class LearningSessionStrategy(BaseDocumentStrategy):
    """Strategy for compiling educational/tutoring conversations into textbook chapters."""

    name = "Learning Session Strategy"
    theme = "academic"

    def build_document(
        self,
        conversation: Conversation,
        profile: ConversationProfile,
    ) -> SemanticDocument:
        """Compile a learning conversation into a structured study guide / book."""
        title = conversation.title or "Study Guide & Course Material"
        sections: list[DocumentSection] = []

        messages = list(conversation.messages)
        assistant_turns = [m for m in messages if str(m.role).lower() == "assistant"]

        sec_offset = 1
        for assistant_msg in assistant_turns:
            a_idx = messages.index(assistant_msg)
            prompt_msg = messages[a_idx - 1] if a_idx > 0 and str(messages[a_idx - 1].role).lower() == "user" else None
            sub_secs = self._turn_to_sections(sec_offset, prompt_msg, assistant_msg, messages, kicker_prefix="Chapter")
            sections.extend(sub_secs)
            sec_offset += len(sub_secs)

        metadata = DocumentMetadata(
            title=title,
            subtitle="Intelligent Study Notes & Knowledge Guide",
            category=ConversationCategory.LEARNING,
            profile=ExportProfile.STUDY_NOTES,
            platform=conversation.platform,
            source_url=conversation.metadata.source_url or conversation.metadata.final_url or "",
            total_sections=len(sections),
        )

        return SemanticDocument(
            metadata=metadata,
            sections=sections,
            theme=self.theme,
        )
