"""Domain enumerations for PaperChat v2."""

from enum import StrEnum


class Platform(StrEnum):
    """Supported conversation platforms."""

    UNKNOWN = "unknown"
    CHATGPT = "chatgpt"
    CLAUDE = "claude"
    GEMINI = "gemini"
    PERPLEXITY = "perplexity"


class ConversationCategory(StrEnum):
    """Automatic conversation classification categories."""

    LEARNING = "learning"
    PROGRAMMING = "programming"
    DEBUGGING = "debugging"
    RESEARCH = "research"
    BRAINSTORMING = "brainstorming"
    BUSINESS = "business"
    MEETING = "meeting"
    INTERVIEW_PREP = "interview_prep"
    GENERAL_QA = "general_qa"


class ExportProfile(StrEnum):
    """Document export profiles."""

    AUTO = "auto"
    STUDY_NOTES = "study_notes"
    DEVELOPER_DOCS = "developer_docs"
    RESEARCH_PAPER = "research_paper"
    EXECUTIVE_REPORT = "executive_report"
    MEETING_MINUTES = "meeting_minutes"
    CHEAT_SHEET = "cheat_sheet"
