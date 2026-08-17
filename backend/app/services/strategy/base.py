from abc import ABC, abstractmethod
import re

from app.domain.conversation import Conversation
from app.domain.message import Message
from app.domain.semantic_document import (
    DocumentElement,
    DocumentSection,
    ElementKind,
    SemanticDocument,
)
from app.services.cleaner.content_cleaner import ContentCleaner
from app.services.intelligence.analyzer import ConversationProfile


class BaseDocumentStrategy(ABC):
    """Base class for domain-specific document compilation strategies."""

    name: str = "Base Strategy"
    theme: str = "default"

    def __init__(self, cleaner: ContentCleaner | None = None) -> None:
        """Initialize strategy."""
        self.cleaner = cleaner or ContentCleaner()

    @abstractmethod
    def build_document(
        self,
        conversation: Conversation,
        profile: ConversationProfile,
    ) -> SemanticDocument:
        """Compile a raw conversation into a SemanticDocument."""

    def _turn_to_sections(
        self,
        index_offset: int,
        prompt_msg: Message | None,
        assistant_msg: Message,
        all_messages: list[Message],
        kicker_prefix: str = "Section",
    ) -> list[DocumentSection]:
        """Convert a real user prompt and assistant response into one or more structured DocumentSections."""
        resp_text = self.cleaner.clean_text(assistant_msg.plain_text, strip_fluff=True)
        resp_text = self.cleaner.deduplicate_code_blocks(resp_text)

        sub_heading_matches = list(re.finditer(r"^(?:#{1,3}\s+)(?:\d+[\.\)]\s*)?([^\n]+)", resp_text, re.MULTILINE))

        if len(sub_heading_matches) >= 2:
            sections: list[DocumentSection] = []
            sec_counter = index_offset
            for i, match in enumerate(sub_heading_matches):
                title = match.group(1).strip()
                start_pos = match.start()
                end_pos = sub_heading_matches[i + 1].start() if i + 1 < len(sub_heading_matches) else len(resp_text)
                chunk_text = resp_text[start_pos:end_pos].strip()

                elements: list[DocumentElement] = []
                if i == 0 and prompt_msg and prompt_msg.plain_text.strip():
                    clean_prompt = self.cleaner.clean_text(prompt_msg.plain_text, strip_fluff=True)
                    elements.append(
                        DocumentElement(
                            kind=ElementKind.CALLOUT,
                            content=clean_prompt,
                            metadata={"label": "User Query"},
                        )
                    )

                parts = re.split(r"(```[\s\S]*?```)", chunk_text)
                for part in parts:
                    p_strip = part.strip()
                    if not p_strip:
                        continue
                    if p_strip.startswith("```"):
                        lang_match = re.match(r"^```(\w*)", p_strip)
                        lang = lang_match.group(1) if lang_match else ""
                        code_body = re.sub(r"^```\w*\n?|\n?```$", "", p_strip)
                        elements.append(
                            DocumentElement(
                                kind=ElementKind.CODE_BLOCK,
                                content=code_body,
                                metadata={"language": lang},
                            )
                        )
                    else:
                        elements.append(
                            DocumentElement(
                                kind=ElementKind.PARAGRAPH,
                                content=p_strip,
                            )
                        )

                sections.append(
                    DocumentSection(
                        id=f"sec-{sec_counter:02d}",
                        title=title,
                        kicker=f"{kicker_prefix} {sec_counter:02d}",
                        elements=elements,
                    )
                )
                sec_counter += 1
            return sections

        return [self._turn_to_section(index_offset, prompt_msg, assistant_msg, all_messages, kicker_prefix)]

    def _turn_to_section(
        self,
        index: int,
        prompt_msg: Message | None,
        assistant_msg: Message,
        all_messages: list[Message],
        kicker_prefix: str = "Section",
    ) -> DocumentSection:
        """Convert a real user prompt and assistant response into a structured DocumentSection."""
        title = self._smart_section_title(prompt_msg, assistant_msg, index)
        sec_id = f"sec-{index:02d}"
        elements: list[DocumentElement] = []

        if prompt_msg and prompt_msg.plain_text.strip():
            clean_prompt = self.cleaner.clean_text(prompt_msg.plain_text, strip_fluff=True)
            elements.append(
                DocumentElement(
                    kind=ElementKind.CALLOUT,
                    content=clean_prompt,
                    metadata={"label": "User Query"},
                )
            )

        resp_text = self.cleaner.clean_text(assistant_msg.plain_text, strip_fluff=True)
        resp_text = self.cleaner.deduplicate_code_blocks(resp_text)

        parts = re.split(r"(```[\s\S]*?```)", resp_text)
        for part in parts:
            p_strip = part.strip()
            if not p_strip:
                continue
            if p_strip.startswith("```"):
                lang_match = re.match(r"^```(\w*)", p_strip)
                lang = lang_match.group(1) if lang_match else ""
                code_body = re.sub(r"^```\w*\n?|\n?```$", "", p_strip)
                elements.append(
                    DocumentElement(
                        kind=ElementKind.CODE_BLOCK,
                        content=code_body,
                        metadata={"language": lang},
                    )
                )
            elif "check for understanding" in p_strip.lower() or "quiz" in p_strip.lower():
                elements.append(
                    DocumentElement(
                        kind=ElementKind.QUIZ_ITEM,
                        content=p_strip,
                    )
                )
            elif "takeaway" in p_strip.lower() or "key concept" in p_strip.lower():
                elements.append(
                    DocumentElement(
                        kind=ElementKind.KEY_TAKEAWAYS,
                        content=p_strip,
                    )
                )
            else:
                elements.append(
                    DocumentElement(
                        kind=ElementKind.PARAGRAPH,
                        content=p_strip,
                    )
                )

        return DocumentSection(
            id=sec_id,
            title=title,
            kicker=f"{kicker_prefix} {index:02d}",
            elements=elements,
        )

    def _smart_section_title(
        self,
        prompt_msg: Message | None,
        assistant_msg: Message,
        index: int,
    ) -> str:
        """Extract a clean, human-readable section title from real assistant or prompt text."""
        # 1. Look for explicit headings in assistant response (e.g. "Topic 1: Types of Data")
        resp_text = assistant_msg.plain_text.strip()
        topic_match = re.search(
            r"^(?:#{1,4}\s+)?(?:Topic\s+\d+:?|Section\s+\d+:?|[A-Z0-9\.\s-]+:)\s*([^\n]+)",
            resp_text,
            re.MULTILINE | re.IGNORECASE,
        )
        if topic_match:
            clean_heading = topic_match.group(0).strip().lstrip("#").strip()
            if 4 < len(clean_heading) < 90 and not clean_heading.lower().startswith("you said"):
                return clean_heading

        # 2. Look for prompt question text
        if prompt_msg and prompt_msg.plain_text.strip():
            raw_p = prompt_msg.plain_text.strip()
            for prefix in ("you said:", "you said", "user:", "prompt:", "q:", "question:"):
                if raw_p.lower().startswith(prefix):
                    raw_p = raw_p[len(prefix):].strip()
            normalized = " ".join(raw_p.split())
            if normalized and len(normalized) <= 85 and not any(k in normalized.lower() for k in ("you are an expert", "system prompt")):
                return normalized[0].upper() + normalized[1:]

        return f"Topic {index}: Core Insights & Concepts"
