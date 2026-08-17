"""Central Semantic Document Model (SDM) for PaperChat v2."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from app.domain.enums import ConversationCategory, ExportProfile, Platform


class ElementKind(StrEnum):
    """Semantic element types in compiled documents."""

    PARAGRAPH = "paragraph"
    HEADING = "heading"
    CODE_BLOCK = "code_block"
    CALLOUT = "callout"
    KEY_TAKEAWAYS = "key_takeaways"
    TABLE = "table"
    QUIZ_ITEM = "quiz_item"
    ACTION_ITEM = "action_item"
    MATH_FORMULA = "math_formula"
    GLOSSARY_ITEM = "glossary_item"


@dataclass(frozen=True)
class DocumentElement:
    """A single semantic element within a document section."""

    kind: ElementKind
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentSection:
    """A logical section or chapter in a compiled document."""

    id: str
    title: str
    kicker: str = ""
    elements: list[DocumentElement] = field(default_factory=list)
    subsections: list["DocumentSection"] = field(default_factory=list)


@dataclass
class DocumentMetadata:
    """Metadata describing the compiled document."""

    title: str
    subtitle: str
    category: ConversationCategory
    profile: ExportProfile
    platform: Platform
    source_url: str = ""
    generated_date: str = ""
    reading_time_minutes: int = 1
    total_sections: int = 0
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticDocument:
    """The central intermediate document representation for PaperChat v2.

    Decouples raw conversation turns from publishing and rendering.
    """

    metadata: DocumentMetadata
    sections: list[DocumentSection] = field(default_factory=list)
    theme: str = "default"
    show_cover: bool = True
    show_headers: bool = True
