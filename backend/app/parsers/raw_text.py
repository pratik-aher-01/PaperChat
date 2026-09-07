"""Parser for pasted raw text and markdown conversation transcripts."""

import re
from uuid import uuid4

from app.domain.content_block import ContentBlock
from app.domain.conversation import Conversation
from app.domain.enums import Platform
from app.domain.message import Message
from app.domain.metadata import ConversationMetadata
from exceptions import ParserException

USER_PREFIXES = (
    r"^(?:user|human|you|me|prompt|question|q)\s*:\s*",
    r"^#{1,4}\s*(?:user|human|you|question|q)\s*:\s*",
)

ASSISTANT_PREFIXES = (
    r"^(?:assistant|chatgpt|claude|gemini|perplexity|ai|model|answer|a)\s*:\s*",
    r"^#{1,4}\s*(?:assistant|chatgpt|claude|gemini|ai|answer|a)\s*:\s*",
)


class RawTextParser:
    """Parse unformatted or markdown text into a normalized Conversation."""

    def parse(self, raw_text: str, default_title: str = "Pasted Conversation") -> Conversation:
        """Convert raw conversation text into structured messages."""
        text = raw_text.strip()
        if not text:
            raise ParserException("Cannot parse empty text.")

        messages = self._extract_turns(text)
        if not messages:
            raise ParserException("Could not extract any conversational turns from the provided text.")

        # Determine smart title from first user prompt
        first_user = next((m for m in messages if m.role == "user"), messages[0])
        first_line = first_user.plain_text.splitlines()[0] if first_user.plain_text else ""
        clean_title = re.sub(r"^[#\s\-\*]+", "", first_line).strip()[:100]
        title = clean_title or default_title

        metadata = ConversationMetadata(
            source_url="pasted-text",
            final_url="pasted-text",
            title=title,
            raw_html=text,
            fetch_time_ms=0,
        )

        return Conversation(
            platform=Platform.CUSTOM,
            title=title,
            messages=tuple(messages),
            metadata=metadata,
            raw_html=text,
        )

    def _extract_turns(self, text: str) -> list[Message]:
        """Extract user and assistant messages from raw transcript text."""
        # Check if text contains explicit role labels (User: / Assistant: etc.)
        labeled_messages = self._parse_labeled_turns(text)
        if len(labeled_messages) >= 2:
            return labeled_messages

        # Fallback: parse markdown heading sections (# Q1 / # Q2)
        heading_messages = self._parse_heading_turns(text)
        if len(heading_messages) >= 2:
            return heading_messages

        # Fallback: alternating double newline blocks
        return self._parse_block_turns(text)

    def _parse_labeled_turns(self, text: str) -> list[Message]:
        """Split text by recognized role prefix lines."""
        lines = text.splitlines()
        messages: list[Message] = []
        current_role: str | None = None
        current_lines: list[str] = []

        for line in lines:
            role = self._match_role_line(line)
            if role is not None:
                # Flush previous message
                if current_role and current_lines:
                    msg_text = "\n".join(current_lines).strip()
                    if msg_text:
                        messages.append(self._build_message(current_role, msg_text))
                current_role = role
                # Strip prefix from first line
                cleaned_line = self._strip_prefix(line, role)
                current_lines = [cleaned_line] if cleaned_line else []
            else:
                current_lines.append(line)

        # Flush final message
        if current_role and current_lines:
            msg_text = "\n".join(current_lines).strip()
            if msg_text:
                messages.append(self._build_message(current_role, msg_text))

        return messages

    def _parse_heading_turns(self, text: str) -> list[Message]:
        """Split text by markdown headings (# Question / ## Prompt)."""
        sections = re.split(r"(?m)^(#{1,3}\s+.+)$", text)
        messages: list[Message] = []

        i = 1
        while i < len(sections):
            heading = sections[i].strip()
            content = sections[i + 1].strip() if i + 1 < len(sections) else ""
            if heading and content:
                # Heading is user question, content is assistant answer
                messages.append(self._build_message("user", heading))
                messages.append(self._build_message("assistant", content))
            i += 2

        return messages

    def _parse_block_turns(self, text: str) -> list[Message]:
        """Split text by paragraphs, alternating user and assistant."""
        blocks = [b.strip() for b in re.split(r"\n{2,}", text) if b.strip()]
        if not blocks:
            return []

        if len(blocks) == 1:
            # Single block: treat first line as prompt, remainder as assistant answer
            lines = blocks[0].split("\n", 1)
            prompt = lines[0].strip()
            answer = lines[1].strip() if len(lines) > 1 else prompt
            return [
                self._build_message("user", prompt),
                self._build_message("assistant", answer),
            ]

        messages: list[Message] = []
        for index, block in enumerate(blocks):
            role = "user" if index % 2 == 0 else "assistant"
            messages.append(self._build_message(role, block))

        return messages

    def _match_role_line(self, line: str) -> str | None:
        """Check if line starts with a recognized user or assistant prefix."""
        stripped = line.strip().lower()
        for p in USER_PREFIXES:
            if re.match(p, stripped, re.IGNORECASE):
                return "user"
        for p in ASSISTANT_PREFIXES:
            if re.match(p, stripped, re.IGNORECASE):
                return "assistant"
        return None

    def _strip_prefix(self, line: str, role: str) -> str:
        """Remove the role prefix from a line."""
        prefixes = USER_PREFIXES if role == "user" else ASSISTANT_PREFIXES
        for p in prefixes:
            match = re.match(p, line.strip(), re.IGNORECASE)
            if match:
                return line.strip()[match.end():].strip()
        return line.strip()

    def _build_message(self, role: str, text: str) -> Message:
        """Create a Message domain object."""
        return Message(
            id=f"msg-{uuid4().hex[:8]}",
            role=role,
            plain_text=text,
            content_blocks=(ContentBlock(type="markdown", text=text),),
        )
