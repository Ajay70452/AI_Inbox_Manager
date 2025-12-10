"""
Email Thread Summarization Service

This service handles generating and storing AI summaries for email threads.
"""

import logging
from sqlalchemy.orm import Session
from typing import Optional

from models import Thread, AIThreadSummary, User
from services.ai_orchestrator import AIOrchestrator

logger = logging.getLogger(__name__)


class SummarizationService:
    """Service for email thread summarization"""

    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.orchestrator = AIOrchestrator(db, user)

    def summarize_thread(self, thread_id: str, force_regenerate: bool = False) -> AIThreadSummary:
        """
        Generate or retrieve summary for email thread

        Args:
            thread_id: Thread ID (UUID or Provider ID)
            force_regenerate: If True, regenerate even if summary exists

        Returns:
            AIThreadSummary instance
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

        # Check if summary already exists
        existing_summary = (
            self.db.query(AIThreadSummary)
            .filter(AIThreadSummary.thread_id == internal_thread_id)
            .first()
        )

        if existing_summary and not force_regenerate:
            logger.info(f"Using existing summary for thread {internal_thread_id}")
            return existing_summary

        # Generate new summary
        logger.info(f"Generating new summary for thread {internal_thread_id}")
        result = self.orchestrator.summarize_thread(internal_thread_id)

        # Save or update in database
        if existing_summary:
            existing_summary.summary_text = result["summary_text"]
            existing_summary.model_used = result["model_used"]
            summary = existing_summary
        else:
            summary = AIThreadSummary(
                thread_id=thread_id,
                summary_text=result["summary_text"],
                model_used=result["model_used"]
            )
            self.db.add(summary)

        self.db.commit()
        self.db.refresh(summary)

        logger.info(f"Summary saved for thread {thread_id}")
        return summary
