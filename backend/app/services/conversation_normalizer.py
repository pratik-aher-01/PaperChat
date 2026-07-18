"""Conversation normalization service."""

import re

from app.domain.conversation import Conversation
from app.domain.content_block import ContentBlock
from app.domain.message import Message


class ConversationNormalizer:
    """Normalize extracted conversations without destroying formatting."""

    def normalize(self, conversation: Conversation) -> Conversation:
        """Normalize conversation messages and title."""
        messages = tuple(self._normalize_message(message) for message in conversation.messages)
        return Conversation(
            platform=conversation.platform,
            title=self._normalize_inline_text(conversation.title),
            messages=messages,
            metadata=conversation.metadata,
            raw_html=conversation.raw_html,
        )

    def _normalize_message(self, message: Message) -> Message:
        """Normalize a single message."""
        plain_text = self.normalize_markdown_text(message.plain_text)
        blocks = tuple(
            ContentBlock(type=block.type, text=self.normalize_markdown_text(block.text))
            for block in message.content_blocks
        )
        return Message(
            id=message.id,
            role=message.role,
            plain_text=plain_text,
            content_blocks=blocks,
        )

    def normalize_markdown_text(self, value: str) -> str:
        """Normalize whitespace while preserving markdown structures."""
        value = value.replace("\r\n", "\n").replace("\r", "\n")
        value = self._normalize_outside_code_blocks(value)
        value = re.sub(r"\n{3,}", "\n\n", value)
        return value.strip()

    def _normalize_outside_code_blocks(self, value: str) -> str:
        """Normalize text outside fenced code blocks."""
        parts = re.split(r"(```[\s\S]*?```)", value)
        normalized_parts: list[str] = []
        for part in parts:
            if part.startswith("```") and part.endswith("```"):
                normalized_parts.append(part.strip("\n"))
                continue
            normalized_parts.append(self._normalize_markdown_segment(part))
        return "".join(normalized_parts)

    def _normalize_markdown_segment(self, value: str) -> str:
        """Normalize a markdown segment that is not a code block."""
        lines = [self._normalize_line(line) for line in value.split("\n")]
        return "\n".join(lines)

    def _normalize_line(self, line: str) -> str:
        """Normalize one non-code markdown line."""
        stripped = line.strip()
        if not stripped:
            return ""
        list_match = re.match(r"^(\s*)((?:[-*+])|\d+\.)\s+(.*)$", line)
        if list_match:
            indent, marker, content = list_match.groups()
            content = re.sub(r"[ \t]+", " ", content.strip())
            return f"{indent}{marker} {content}"
        return re.sub(r"[ \t]+", " ", stripped)

    def _normalize_inline_text(self, value: str) -> str:
        """Normalize inline text."""
        return re.sub(r"\s+", " ", value).strip()
