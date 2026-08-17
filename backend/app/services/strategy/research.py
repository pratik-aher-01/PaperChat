"""Research document compilation strategy."""

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


class ResearchStrategy(BaseDocumentStrategy):
    """Strategy for compiling research conversations into a research paper/report."""

    name = "Research Strategy"
    theme = "minimal"

    def build_document(
        self,
        conversation: Conversation,
        profile: ConversationProfile,
    ) -> SemanticDocument:
        """Compile research conversation into a research paper."""
        title = conversation.title or "Research Paper & Literature Review"
        sections: list[DocumentSection] = []
        last_user_msg: Message | None = None
        turn_idx = 1
        for msg in conversation.messages:
            if str(msg.role).lower() == "user":
                last_user_msg = msg
            elif str(msg.role).lower() == "assistant":
                sec = self._turn_to_section(turn_idx, last_user_msg, msg, list(conversation.messages), kicker_prefix="Section")
                sections.append(sec)
                turn_idx += 1
                last_user_msg = None

        metadata = DocumentMetadata(
            title=title,
            subtitle="Research Paper & Findings Report",
            category=ConversationCategory.RESEARCH,
            profile=ExportProfile.RESEARCH_PAPER,
            platform=conversation.platform,
            source_url=conversation.metadata.source_url or conversation.metadata.final_url or "",
            total_sections=len(sections),
        )

        return SemanticDocument(
            metadata=metadata,
            sections=sections,
            theme=self.theme,
        )
