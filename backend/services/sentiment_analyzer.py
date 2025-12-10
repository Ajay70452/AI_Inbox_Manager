"""
Email Sentiment Analysis Service

This service handles AI-powered sentiment analysis of email threads.
"""

import logging
from sqlalchemy.orm import Session

from models import AISentiment, User, Thread
from services.ai_orchestrator import AIOrchestrator

logger = logging.getLogger(__name__)


class SentimentAnalysisService:
    """Service for email sentiment analysis"""

    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.orchestrator = AIOrchestrator(db, user)

    def analyze_thread(self, thread_id: str, force_regenerate: bool = False) -> AISentiment:
        """
        Analyze sentiment of email thread

        Args:
            thread_id: Thread ID (UUID or Provider ID)
            force_regenerate: If True, regenerate even if analysis exists

        Returns:
            AISentiment instance
        """
        # Resolve thread_id to internal UUID
        thread = None
        try:
            thread = self.db.query(Thread).filter(Thread.id == thread_id).first()
        except Exception:
            self.db.rollback()
            pass
            
        if not thread:
            thread = self.db.query(Thread).filter(Thread.thread_id_provider == thread_id).first()
            
        if not thread:
            raise ValueError(f"Thread not found: {thread_id}")
            
        internal_thread_id = str(thread.id)

        # Check if sentiment analysis already exists
        existing_sentiment = (
            self.db.query(AISentiment)
            .filter(AISentiment.thread_id == internal_thread_id)
            .first()
        )

        if existing_sentiment and not force_regenerate:
            logger.info(f"Using existing sentiment analysis for thread {internal_thread_id}")
            return existing_sentiment

        # Generate new sentiment analysis
        logger.info(f"Analyzing sentiment for thread {internal_thread_id}")
        result = self.orchestrator.analyze_sentiment(internal_thread_id)

        # Save or update in database
        if existing_sentiment:
            existing_sentiment.sentiment_score = result["sentiment_score"]
            existing_sentiment.sentiment_label = result["sentiment_label"]
            existing_sentiment.anger_level = result["anger_level"]
            existing_sentiment.urgency_score = result["urgency_score"]
            sentiment = existing_sentiment
        else:
            sentiment = AISentiment(
                thread_id=thread_id,
                sentiment_score=result["sentiment_score"],
                sentiment_label=result["sentiment_label"],
                anger_level=result["anger_level"],
                urgency_score=result["urgency_score"]
            )
            self.db.add(sentiment)

        self.db.commit()
        self.db.refresh(sentiment)

        logger.info(
            f"Sentiment analysis saved for thread {thread_id}: "
            f"{sentiment.sentiment_label} (score: {sentiment.sentiment_score:.2f})"
        )
        return sentiment
