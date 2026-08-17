"""Document strategy engine selector."""

from app.domain.enums import ConversationCategory, ExportProfile
from app.services.strategy.base import BaseDocumentStrategy
from app.services.strategy.business import BusinessStrategy
from app.services.strategy.learning import LearningSessionStrategy
from app.services.strategy.meeting import MeetingStrategy
from app.services.strategy.programming import ProgrammingSessionStrategy
from app.services.strategy.research import ResearchStrategy


class StrategyEngine:
    """Select the appropriate document compilation strategy based on category or profile override."""

    def __init__(self) -> None:
        """Initialize available strategies."""
        self._strategies: dict[ConversationCategory, BaseDocumentStrategy] = {
            ConversationCategory.LEARNING: LearningSessionStrategy(),
            ConversationCategory.PROGRAMMING: ProgrammingSessionStrategy(),
            ConversationCategory.DEBUGGING: ProgrammingSessionStrategy(),
            ConversationCategory.RESEARCH: ResearchStrategy(),
            ConversationCategory.BRAINSTORMING: BusinessStrategy(),
            ConversationCategory.BUSINESS: BusinessStrategy(),
            ConversationCategory.MEETING: MeetingStrategy(),
            ConversationCategory.INTERVIEW_PREP: LearningSessionStrategy(),
            ConversationCategory.GENERAL_QA: LearningSessionStrategy(),
        }

        self._profile_map: dict[ExportProfile, BaseDocumentStrategy] = {
            ExportProfile.STUDY_NOTES: LearningSessionStrategy(),
            ExportProfile.DEVELOPER_DOCS: ProgrammingSessionStrategy(),
            ExportProfile.RESEARCH_PAPER: ResearchStrategy(),
            ExportProfile.EXECUTIVE_REPORT: BusinessStrategy(),
            ExportProfile.MEETING_MINUTES: MeetingStrategy(),
            ExportProfile.CHEAT_SHEET: LearningSessionStrategy(),
        }

    def get_strategy(
        self,
        category: ConversationCategory,
        profile_override: ExportProfile = ExportProfile.AUTO,
    ) -> BaseDocumentStrategy:
        """Return the strategy matching profile override or detected category."""
        if profile_override != ExportProfile.AUTO and profile_override in self._profile_map:
            return self._profile_map[profile_override]

        return self._strategies.get(category, LearningSessionStrategy())
