"""Automatic conversation classification service."""

from app.domain.enums import ConversationCategory
from app.services.intelligence.analyzer import ConversationProfile


class ConversationClassifier:
    """Classify conversations into domain categories based on analytical signals."""

    def classify(self, profile: ConversationProfile, title: str = "") -> ConversationCategory:
        """Determine the most appropriate category for a conversation."""
        title_lower = title.lower()

        # Check explicit title signals
        if any(w in title_lower for w in ("meeting", "sync", "standup", "minutes")):
            return ConversationCategory.MEETING

        if any(w in title_lower for w in ("interview", "job prep", "behavioral question")):
            return ConversationCategory.INTERVIEW_PREP

        if profile.has_quiz_patterns or len(profile.detected_topics) > 1:
            return ConversationCategory.LEARNING

        if profile.has_debugging_patterns and profile.code_ratio > 0.2:
            return ConversationCategory.DEBUGGING

        if profile.code_ratio > 0.25 or profile.code_blocks_count >= 3:
            return ConversationCategory.PROGRAMMING

        if profile.has_research_patterns:
            return ConversationCategory.RESEARCH

        if profile.has_business_patterns:
            return ConversationCategory.BUSINESS

        if profile.has_meeting_patterns:
            return ConversationCategory.MEETING

        if profile.code_blocks_count >= 1:
            return ConversationCategory.PROGRAMMING

        return ConversationCategory.GENERAL_QA
