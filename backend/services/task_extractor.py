"""
Task Extraction Service

This service handles AI-powered extraction of action items and tasks from emails.
"""

import logging
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from models import Task, User, Thread
from services.ai_orchestrator import AIOrchestrator

logger = logging.getLogger(__name__)


class TaskExtractionService:
    """Service for extracting tasks from emails"""

    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.orchestrator = AIOrchestrator(db, user)

    def extract_tasks(
        self,
        thread_id: str,
        force_regenerate: bool = False
    ) -> List[Task]:
        """
        Extract action items and tasks from email thread

        Args:
            thread_id: Thread ID (UUID or Provider ID)
            force_regenerate: If True, regenerate even if tasks exist

        Returns:
            List of Task instances
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

        # Check if tasks already exist
        existing_tasks = (
            self.db.query(Task)
            .filter(Task.thread_id == internal_thread_id)
            .all()
        )

        if existing_tasks and not force_regenerate:
            logger.info(f"Using existing tasks for thread {internal_thread_id}")
            return existing_tasks

        # Delete old tasks if regenerating
        if existing_tasks and force_regenerate:
            for task in existing_tasks:
                self.db.delete(task)
            self.db.commit()

        # Extract tasks using AI
        logger.info(f"Extracting tasks from thread {thread_id}")
        task_data_list = self.orchestrator.extract_tasks(thread_id)

        # Create Task instances
        tasks = []
        for task_data in task_data_list:
            # Parse due date if provided
            due_date = None
            if task_data.get("due_date"):
                try:
                    due_date = datetime.fromisoformat(task_data["due_date"])
                except (ValueError, TypeError):
                    logger.warning(f"Invalid due date: {task_data.get('due_date')}")

            task = Task(
                thread_id=thread_id,
                title=task_data.get("title", "Untitled task"),
                description=task_data.get("description"),
                due_date=due_date,
                extracted_owner=task_data.get("extracted_owner"),
                status="pending"
            )
            self.db.add(task)
            tasks.append(task)

        self.db.commit()

        # Refresh all tasks
        for task in tasks:
            self.db.refresh(task)

        logger.info(f"Extracted {len(tasks)} tasks from thread {thread_id}")
        return tasks

    def update_task_status(self, task_id: str, status: str) -> Task:
        """
        Update task status

        Args:
            task_id: Task ID
            status: New status (pending, completed, cancelled)

        Returns:
            Updated Task instance
        """
        task = self.db.query(Task).filter(Task.id == task_id).first()

        if not task:
            raise ValueError(f"Task {task_id} not found")

        task.status = status
        self.db.commit()
        self.db.refresh(task)

        logger.info(f"Task {task_id} status updated to: {status}")
        return task
