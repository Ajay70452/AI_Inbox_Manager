"""
Email Priority Classification Service

This service handles AI-powered priority classification of email threads.
"""

import logging
from sqlalchemy.orm import Session

from models import AIPriority, User, Thread
from services.ai_orchestrator import AIOrchestrator

logger = logging.getLogger(__name__)


class ClassificationService:
    """Service for email priority classification"""

    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.orchestrator = AIOrchestrator(db, user)

    def classify_thread(self, thread_id: str, force_regenerate: bool = False) -> AIPriority:
        """
        Classify priority of email thread

        Args:
            thread_id: Thread ID (UUID or Provider ID)
            force_regenerate: If True, regenerate even if classification exists

        Returns:
            AIPriority instance
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

        # Check if classification already exists
        existing_priority = (
            self.db.query(AIPriority)
            .filter(AIPriority.thread_id == internal_thread_id)
            .first()
        )

        if existing_priority and not force_regenerate:
            logger.info(f"Using existing classification for thread {internal_thread_id}")
            return existing_priority

        # Generate new classification
        logger.info(f"Classifying thread {internal_thread_id}")
        result = self.orchestrator.classify_priority(internal_thread_id)

        # Save or update in database
        if existing_priority:
            existing_priority.priority_level = result["priority_level"]
            existing_priority.category = result["category"]
            priority = existing_priority
        else:
            priority = AIPriority(
                thread_id=thread_id,
                priority_level=result["priority_level"],
                category=result["category"]
            )
            self.db.add(priority)

        self.db.commit()
        self.db.refresh(priority)

        logger.info(
            f"Priority classification saved for thread {thread_id}: "
            f"{priority.priority_level} - {priority.category}"
        )
        return priority
