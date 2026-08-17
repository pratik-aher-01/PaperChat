"""Main PaperChat v2 Intelligent Conversation Compiler pipeline."""

from app.domain.conversation import Conversation
from app.domain.enums import ExportProfile
from app.domain.semantic_document import SemanticDocument
from app.services.cleaner.content_cleaner import ContentCleaner
from app.services.intelligence.analyzer import ConversationAnalyzer
from app.services.intelligence.classifier import ConversationClassifier
from app.services.strategy.engine import StrategyEngine


class ConversationCompiler:
    """Intelligent Conversation Compiler orchestrating the V2 pipeline."""

    def __init__(
        self,
        analyzer: ConversationAnalyzer | None = None,
        classifier: ConversationClassifier | None = None,
        cleaner: ContentCleaner | None = None,
        strategy_engine: StrategyEngine | None = None,
    ) -> None:
        """Initialize the compiler pipeline."""
        self.analyzer = analyzer or ConversationAnalyzer()
        self.classifier = classifier or ConversationClassifier()
        self.cleaner = cleaner or ContentCleaner()
        self.strategy_engine = strategy_engine or StrategyEngine()

    def compile(
        self,
        conversation: Conversation,
        profile_override: ExportProfile = ExportProfile.AUTO,
        clean_fluff: bool = True,
    ) -> SemanticDocument:
        """Compile a raw Conversation into a SemanticDocument."""
        profile = self.analyzer.analyze(conversation)
        category = self.classifier.classify(profile, title=conversation.title)
        strategy = self.strategy_engine.get_strategy(category, profile_override=profile_override)

        doc = strategy.build_document(conversation, profile)
        return doc
