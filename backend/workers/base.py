"""
Base Worker Class

Foundation for all background workers
"""

import logging
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict
from datetime import datetime

from workers.monitoring import get_monitor, WorkerStatus

logger = logging.getLogger(__name__)


class BaseWorker(ABC):
    """
    Base class for background workers

    All workers should inherit from this class and implement
    the execute() method.
    """

    def __init__(self, name: str):
        """
        Initialize worker

        Args:
            name: Worker name for logging
        """
        self.name = name
        self.logger = logging.getLogger(f"worker.{name}")
        self.monitor = get_monitor()

    @abstractmethod
    def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Execute worker task

        This method must be implemented by subclasses.

        Returns:
            Dictionary with task results
        """
        pass

    def run(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Run worker with error handling and logging

        Args:
            *args: Positional arguments for execute()
            **kwargs: Keyword arguments for execute()

        Returns:
            Dictionary with task results and metadata
        """
        start_time = datetime.utcnow()
        job_id = str(uuid.uuid4())

        self.logger.info(f"Starting worker: {self.name} (job: {job_id})")

        # Record start in monitoring
        self.monitor.record_start(self.name, job_id)

        try:
            result = self.execute(*args, **kwargs)

            duration = (datetime.utcnow() - start_time).total_seconds()
            self.logger.info(
                f"Worker {self.name} completed successfully in {duration:.2f}s"
            )

            # Record successful completion
            self.monitor.record_completion(
                worker_name=self.name,
                job_id=job_id,
                status=WorkerStatus.SUCCESS,
                duration=duration,
                result_summary=self._summarize_result(result)
            )

            return {
                'status': 'success',
                'worker': self.name,
                'job_id': job_id,
                'duration': duration,
                'result': result,
                'started_at': start_time.isoformat(),
                'completed_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.logger.error(
                f"Worker {self.name} failed after {duration:.2f}s: {str(e)}",
                exc_info=True
            )

            # Record failure
            self.monitor.record_completion(
                worker_name=self.name,
                job_id=job_id,
                status=WorkerStatus.FAILED,
                duration=duration,
                error_message=str(e)
            )

            return {
                'status': 'failed',
                'worker': self.name,
                'job_id': job_id,
                'duration': duration,
                'error': str(e),
                'started_at': start_time.isoformat(),
                'failed_at': datetime.utcnow().isoformat()
            }

    def _summarize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a summary of the result for monitoring

        Args:
            result: Full result dictionary

        Returns:
            Summarized result
        """
        # Extract key metrics for monitoring
        summary = {}

        # Common fields to track
        if isinstance(result, dict):
            for key in ['total_emails', 'total_threads', 'threads_processed',
                       'threads_failed', 'users_synced', 'users_failed']:
                if key in result:
                    summary[key] = result[key]

        return summary
