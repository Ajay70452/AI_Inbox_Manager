"""
AI Reply Generation Service

This service handles AI-powered auto-reply draft generation.
"""

import logging
from sqlalchemy.orm import Session
from typing import Optional

from models import AIReplyDraft, User, Thread
from services.ai_orchestrator import AIOrchestrator

logger = logging.getLogger(__name__)


class ReplyGenerationService:
    """Service for AI reply generation"""

    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.orchestrator = AIOrchestrator(db, user)

    def generate_reply(
        self,
        thread_id: str,
        tone: Optional[str] = None,
        force_regenerate: bool = False
    ) -> AIReplyDraft:
        """
        Generate AI reply draft for email thread

        Args:
            thread_id: Thread ID (UUID or Provider ID)
            tone: Desired tone (professional, friendly, formal, concise)
            force_regenerate: If True, regenerate even if draft exists

        Returns:
            AIReplyDraft instance
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

        # Check if reply draft already exists
        existing_draft = (
            self.db.query(AIReplyDraft)
            .filter(AIReplyDraft.thread_id == internal_thread_id)
            .first()
        )

        if existing_draft and not force_regenerate:
            logger.info(f"Using existing reply draft for thread {internal_thread_id}")
            return existing_draft

        # Generate new reply
        logger.info(f"Generating reply draft for thread {thread_id}")
        result = self.orchestrator.generate_reply(thread_id, tone)

        # Save or update in database
        if existing_draft:
            existing_draft.draft_text = result["draft_text"]
            existing_draft.tone_used = result["tone_used"]
            draft = existing_draft
        else:
            draft = AIReplyDraft(
                thread_id=thread_id,
                draft_text=result["draft_text"],
                tone_used=result["tone_used"]
            )
            self.db.add(draft)

        self.db.commit()
        self.db.refresh(draft)

        logger.info(f"Reply draft saved for thread {thread_id}")
        return draft

    def regenerate_with_style(
        self,
        thread_id: str,
        style: str
    ) -> AIReplyDraft:
        """
        Regenerate reply with different style

        Args:
            thread_id: Thread ID
            style: Style instruction (shorter, longer, more formal, friendlier)

        Returns:
            Updated AIReplyDraft instance
        """
        logger.info(f"Regenerating reply for thread {thread_id} with style: {style}")

        # Get existing draft
        existing_draft = (
            self.db.query(AIReplyDraft)
            .filter(AIReplyDraft.thread_id == thread_id)
            .first()
        )

        if not existing_draft:
            # Generate initial draft first
            return self.generate_reply(thread_id)

        # Rewrite with new style
        rewritten = self.orchestrator.rewrite_reply(
            original_draft=existing_draft.draft_text,
            instruction=style
        )

        # Update draft
        existing_draft.draft_text = rewritten
        existing_draft.tone_used = f"{existing_draft.tone_used} ({style})"

        self.db.commit()
        self.db.refresh(existing_draft)

        logger.info(f"Reply draft regenerated for thread {thread_id}")
        return existing_draft
