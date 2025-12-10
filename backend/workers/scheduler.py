"""
Worker Scheduler

Manages periodic execution of background workers using APScheduler
"""

import logging
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from datetime import datetime

from app.config import settings
from workers.email_sync_worker import sync_all_users
from workers.ai_processing_worker import process_all_unprocessed_threads

logger = logging.getLogger(__name__)


class WorkerScheduler:
    """
    Scheduler for background workers

    Manages periodic execution of email sync and AI processing tasks
    """

    def __init__(self):
        """Initialize scheduler"""
        self.scheduler = BackgroundScheduler(
            timezone='UTC',
            job_defaults={
                'coalesce': True,  # Combine multiple pending executions into one
                'max_instances': 1,  # Only one instance of each job at a time
                'misfire_grace_time': 300  # 5 minutes grace period
            }
        )

        # Add event listeners
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED
        )
        self.scheduler.add_listener(
            self._job_error_listener,
            EVENT_JOB_ERROR
        )

        self._is_running = False
        logger.info("Worker scheduler initialized")

    def _job_executed_listener(self, event):
        """Log successful job execution"""
        logger.info(
            f"Job {event.job_id} executed successfully at {datetime.utcnow()}"
        )

    def _job_error_listener(self, event):
        """Log job errors"""
        logger.error(
            f"Job {event.job_id} failed: {event.exception}",
            exc_info=True
        )

    def add_email_sync_job(
        self,
        interval_minutes: Optional[int] = None,
        lookback_days: int = 7
    ):
        """
        Add periodic email sync job

        Args:
            interval_minutes: Sync interval in minutes (from settings if None)
            lookback_days: Days to look back for emails
        """
        interval = interval_minutes or settings.EMAIL_SYNC_INTERVAL_MINUTES

        self.scheduler.add_job(
            func=sync_all_users,
            trigger=IntervalTrigger(minutes=interval),
            args=[lookback_days],
            id='email_sync_job',
            name='Email Sync for All Users',
            replace_existing=True
        )

        logger.info(
            f"Scheduled email sync job: every {interval} minutes, "
            f"lookback {lookback_days} days"
        )

    def add_ai_processing_job(
        self,
        interval_minutes: Optional[int] = None,
        limit: int = 50
    ):
        """
        Add periodic AI processing job

        Args:
            interval_minutes: Processing interval in minutes (from settings if None)
            limit: Maximum threads to process per run
        """
        interval = interval_minutes or settings.AI_PROCESSING_INTERVAL_MINUTES

        self.scheduler.add_job(
            func=process_all_unprocessed_threads,
            trigger=IntervalTrigger(minutes=interval),
            kwargs={'limit': limit},
            id='ai_processing_job',
            name='AI Processing for Unprocessed Threads',
            replace_existing=True
        )

        logger.info(
            f"Scheduled AI processing job: every {interval} minutes, "
            f"limit {limit} threads"
        )

    def add_nightly_cleanup_job(self):
        """
        Add nightly cleanup job at 2 AM UTC

        This job can handle:
        - Cleaning up old sync logs
        - Removing expired tokens
        - Archiving old emails
        """
        self.scheduler.add_job(
            func=self._nightly_cleanup,
            trigger=CronTrigger(hour=2, minute=0),
            id='nightly_cleanup_job',
            name='Nightly Cleanup',
            replace_existing=True
        )

        logger.info("Scheduled nightly cleanup job: 2:00 AM UTC")

    def _nightly_cleanup(self):
        """
        Perform nightly cleanup tasks

        TODO: Implement actual cleanup logic
        """
        logger.info("Running nightly cleanup...")

        # Placeholder for cleanup tasks
        # - Delete sync logs older than 30 days
        # - Remove expired OAuth tokens
        # - Archive processed threads

        logger.info("Nightly cleanup completed")

    def start(self):
        """Start the scheduler"""
        if self._is_running:
            logger.warning("Scheduler is already running")
            return

        # Add default jobs
        # self.add_email_sync_job()  # Disabled: using on-demand processing only
        # self.add_ai_processing_job()  # Disabled to prevent Gemini quota exhaustion
        self.add_nightly_cleanup_job()

        # Start scheduler
        self.scheduler.start()
        self._is_running = True

        logger.info("Worker scheduler started")
        logger.info(f"Scheduled jobs: {len(self.scheduler.get_jobs())}")

        # Log all scheduled jobs
        for job in self.scheduler.get_jobs():
            logger.info(f"  - {job.name} (ID: {job.id}, Next run: {job.next_run_time})")

    def stop(self):
        """Stop the scheduler"""
        if not self._is_running:
            logger.warning("Scheduler is not running")
            return

        self.scheduler.shutdown(wait=True)
        self._is_running = False
        logger.info("Worker scheduler stopped")

    def pause_job(self, job_id: str):
        """
        Pause a specific job

        Args:
            job_id: Job ID to pause
        """
        self.scheduler.pause_job(job_id)
        logger.info(f"Job {job_id} paused")

    def resume_job(self, job_id: str):
        """
        Resume a paused job

        Args:
            job_id: Job ID to resume
        """
        self.scheduler.resume_job(job_id)
        logger.info(f"Job {job_id} resumed")

    def remove_job(self, job_id: str):
        """
        Remove a job from scheduler

        Args:
            job_id: Job ID to remove
        """
        self.scheduler.remove_job(job_id)
        logger.info(f"Job {job_id} removed")

    def get_jobs_info(self) -> list:
        """
        Get information about all scheduled jobs

        Returns:
            List of job information dictionaries
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        return jobs

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self._is_running


# Global scheduler instance
_scheduler_instance: Optional[WorkerScheduler] = None


def get_scheduler() -> WorkerScheduler:
    """
    Get global scheduler instance (singleton)

    Returns:
        WorkerScheduler instance
    """
    global _scheduler_instance

    if _scheduler_instance is None:
        _scheduler_instance = WorkerScheduler()

    return _scheduler_instance


def start_scheduler():
    """Start the global scheduler"""
    scheduler = get_scheduler()
    scheduler.start()


def stop_scheduler():
    """Stop the global scheduler"""
    scheduler = get_scheduler()
    scheduler.stop()
