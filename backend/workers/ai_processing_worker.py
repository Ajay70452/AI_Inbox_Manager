"""
AI Processing Worker

Background worker for AI processing of emails (summarization, classification, etc.)
"""

import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from workers.base import BaseWorker
from models import User, Thread, AccountToken
from services import (
    SummarizationService,
    ClassificationService,
    SentimentAnalysisService,
    ReplyGenerationService,
    TaskExtractionService
)
from services.gmail_service import GmailService
from db import SessionLocal

logger = logging.getLogger(__name__)


class AIProcessingWorker(BaseWorker):
    """Worker for processing individual threads with AI"""

    def __init__(self):
        super().__init__("ai_processing")

    def execute(
        self,
        user_id: str,
        thread_id: str,
        tasks: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process a thread with AI

        Args:
            user_id: User ID
            thread_id: Thread ID to process
            tasks: List of tasks to perform. Options:
                   - 'summarize'
                   - 'classify'
                   - 'sentiment'
                   - 'reply'
                   - 'tasks'
                   If None, performs all tasks

        Returns:
            Processing results
        """
        db = SessionLocal()

        try:
            # Get user and thread
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User not found: {user_id}")

            # Try to find thread by ID (UUID) or Provider ID (String)
            thread = None
            
            # First check if it matches thread_id_provider (most likely from extension)
            thread = db.query(Thread).filter(
                Thread.thread_id_provider == thread_id,
                Thread.user_id == user_id
            ).first()
            
            # If not found, try resolving the ID via Gmail API (it might be an alias)
            if not thread:
                account = db.query(AccountToken).filter(
                    AccountToken.user_id == user_id,
                    AccountToken.provider == 'gmail'
                ).first()
                
                if account:
                    try:
                        gmail_service = GmailService(db, user)
                        canonical_id = gmail_service.resolve_thread_id(thread_id)
                        if canonical_id:
                            self.logger.info(f"Resolved thread ID {thread_id} to canonical ID {canonical_id}")
                            thread = db.query(Thread).filter(
                                Thread.thread_id_provider == canonical_id,
                                Thread.user_id == user_id
                            ).first()
                            # Update thread_id to canonical for subsequent logic
                            if thread:
                                thread_id = canonical_id
                    except Exception as e:
                        self.logger.warning(f"Failed to resolve thread ID: {e}")

            # If still not found and it looks like a UUID, try ID
            if not thread:
                try:
                    thread = db.query(Thread).filter(
                        Thread.id == thread_id,
                        Thread.user_id == user_id
                    ).first()
                except Exception:
                    # Not a valid UUID, ignore
                    db.rollback()
                    # Re-fetch user to ensure it's attached to the new transaction
                    user = db.query(User).filter(User.id == user_id).first()
                    pass
            
            if not thread:
                # Try to sync the thread if it's missing
                self.logger.info(f"Thread {thread_id} not found in DB, attempting to sync...")
                
                # Check user's connected accounts
                account = db.query(AccountToken).filter(
                    AccountToken.user_id == user_id,
                    AccountToken.provider == 'gmail'
                ).first()
                
                if account:
                    try:
                        gmail_service = GmailService(db, user)
                        synced_id = gmail_service.sync_thread(thread_id)
                        if synced_id:
                            # Re-query thread by provider ID (using the canonical ID returned by sync)
                            thread = db.query(Thread).filter(
                                Thread.thread_id_provider == synced_id,
                                Thread.user_id == user_id
                            ).first()
                            
                            if not thread:
                                self.logger.warning(f"Sync reported success (ID: {synced_id}) but thread still not found in DB")
                    except Exception as e:
                        self.logger.error(f"Failed to sync thread during AI processing: {e}")
                
                if not thread:
                    raise ValueError(f"Thread not found: {thread_id}")

            # Update thread_id to the internal UUID for services that need it
            internal_thread_id = str(thread.id)
            
            # Default to only summary and reply tasks to save quota
            if tasks is None:
                tasks = ['summarize', 'reply']

            self.logger.info(
                f"Processing thread {internal_thread_id} (Provider ID: {thread.thread_id_provider}) for user {user.email}: {tasks}"
            )

            results = {}

            # Summarization
            if 'summarize' in tasks:
                try:
                    service = SummarizationService(db, user)
                    summary = service.summarize_thread(internal_thread_id)
                    results['summary'] = {
                        'success': True,
                        'summary_text': summary.summary_text,
                        'model_used': summary.model_used
                    }
                except Exception as e:
                    self.logger.error(f"Summarization failed: {str(e)}")
                    results['summary'] = {'success': False, 'error': str(e)}

            # Classification
            if 'classify' in tasks:
                try:
                    service = ClassificationService(db, user)
                    priority = service.classify_thread(internal_thread_id)
                    results['classification'] = {
                        'success': True,
                        'priority_level': priority.priority_level,
                        'category': priority.category
                    }
                except Exception as e:
                    self.logger.error(f"Classification failed: {str(e)}")
                    results['classification'] = {'success': False, 'error': str(e)}

            # Sentiment Analysis
            if 'sentiment' in tasks:
                try:
                    service = SentimentAnalysisService(db, user)
                    sentiment = service.analyze_thread(internal_thread_id)
                    results['sentiment'] = {
                        'success': True,
                        'sentiment_label': sentiment.sentiment_label,
                        'sentiment_score': sentiment.sentiment_score,
                        'anger_level': sentiment.anger_level,
                        'urgency_score': sentiment.urgency_score
                    }
                except Exception as e:
                    self.logger.error(f"Sentiment analysis failed: {str(e)}")
                    results['sentiment'] = {'success': False, 'error': str(e)}

            # Reply Generation
            if 'reply' in tasks:
                try:
                    service = ReplyGenerationService(db, user)
                    reply = service.generate_reply(internal_thread_id)
                    results['reply'] = {
                        'success': True,
                        'draft_text': reply.draft_text,
                        'tone_used': reply.tone_used
                    }
                except Exception as e:
                    self.logger.error(f"Reply generation failed: {str(e)}")
                    results['reply'] = {'success': False, 'error': str(e)}

            # Task Extraction
            if 'tasks' in tasks:
                try:
                    service = TaskExtractionService(db, user)
                    extracted_tasks = service.extract_tasks(internal_thread_id)
                    results['tasks'] = {
                        'success': True,
                        'task_count': len(extracted_tasks),
                        'tasks': [
                            {
                                'title': task.title,
                                'due_date': task.due_date.isoformat() if task.due_date else None,
                                'owner': task.extracted_owner
                            }
                            for task in extracted_tasks
                        ]
                    }
                except Exception as e:
                    self.logger.error(f"Task extraction failed: {str(e)}")
                    results['tasks'] = {'success': False, 'error': str(e)}

            self.logger.info(f"AI processing completed for thread {internal_thread_id}")
            return results

        finally:
            db.close()


class BulkAIProcessingWorker(BaseWorker):
    """Worker for processing multiple unprocessed threads"""

    def __init__(self):
        super().__init__("bulk_ai_processing")

    def execute(
        self,
        user_id: Optional[str] = None,
        limit: int = 50,
        tasks: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process unprocessed threads with AI

        Args:
            user_id: Specific user ID or None for all users
            limit: Maximum threads to process
            tasks: AI tasks to perform

        Returns:
            Processing statistics
        """
        db = SessionLocal()

        try:
            # Query for threads without AI processing
            query = db.query(Thread)

            if user_id:
                query = query.filter(Thread.user_id == user_id)

            # Get threads without summaries (as proxy for unprocessed)
            from models import AIThreadSummary
            threads = (
                query.outerjoin(AIThreadSummary)
                .filter(AIThreadSummary.id.is_(None))
                .order_by(Thread.last_message_at.desc())
                .limit(limit)
                .all()
            )

            self.logger.info(f"Processing {len(threads)} unprocessed threads")

            stats = {
                'threads_processed': 0,
                'threads_failed': 0,
                'errors': []
            }

            for thread in threads:
                try:
                    # Process this thread
                    worker = AIProcessingWorker()
                    result = worker.run(
                        user_id=str(thread.user_id),
                        thread_id=str(thread.id),
                        tasks=tasks
                    )

                    if result['status'] == 'success':
                        stats['threads_processed'] += 1
                    else:
                        stats['threads_failed'] += 1
                        stats['errors'].append(f"Thread {thread.id}: {result.get('error')}")

                except Exception as e:
                    self.logger.error(f"Failed to process thread {thread.id}: {str(e)}")
                    stats['threads_failed'] += 1
                    stats['errors'].append(f"Thread {thread.id}: {str(e)}")

            self.logger.info(
                f"Bulk AI processing completed: {stats['threads_processed']} threads processed"
            )

            return stats

        finally:
            db.close()


# Standalone functions for RQ/Celery
def process_thread_ai(
    user_id: str,
    thread_id: str,
    tasks: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Process a thread with AI (standalone function for job queues)

    Args:
        user_id: User ID
        thread_id: Thread ID
        tasks: AI tasks to perform

    Returns:
        Processing results
    """
    worker = AIProcessingWorker()
    return worker.run(user_id, thread_id, tasks)


def process_all_unprocessed_threads(
    user_id: Optional[str] = None,
    limit: int = 50,
    tasks: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Process all unprocessed threads (standalone function for job queues)

    Args:
        user_id: Specific user or None for all
        limit: Max threads to process
        tasks: AI tasks to perform

    Returns:
        Processing statistics
    """
    worker = BulkAIProcessingWorker()
    return worker.run(user_id, limit, tasks)
