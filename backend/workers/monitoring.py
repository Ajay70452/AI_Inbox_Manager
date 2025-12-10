"""
Worker Monitoring & Logging

Tracks worker execution metrics and provides monitoring capabilities
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from core.redis_client import get_redis

logger = logging.getLogger(__name__)


class WorkerStatus(str, Enum):
    """Worker execution status"""
    SUCCESS = "success"
    FAILED = "failed"
    RUNNING = "running"
    TIMEOUT = "timeout"


@dataclass
class WorkerMetrics:
    """Worker execution metrics"""
    worker_name: str
    status: WorkerStatus
    started_at: datetime
    completed_at: Optional[datetime]
    duration: Optional[float]
    error_message: Optional[str] = None
    result_summary: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['started_at'] = self.started_at.isoformat()
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        data['status'] = self.status.value
        return data


class WorkerMonitor:
    """
    Monitor and track worker executions

    Stores metrics in Redis for real-time monitoring
    """

    # Redis key prefixes
    METRICS_PREFIX = "worker:metrics"
    STATS_PREFIX = "worker:stats"
    HISTORY_PREFIX = "worker:history"

    # TTL for metrics (7 days)
    METRICS_TTL = 60 * 60 * 24 * 7

    def __init__(self):
        """Initialize monitor"""
        self.redis = get_redis()

    def record_start(self, worker_name: str, job_id: str) -> str:
        """
        Record worker start

        Args:
            worker_name: Name of the worker
            job_id: Unique job ID

        Returns:
            Metrics key for this execution
        """
        metrics_key = f"{self.METRICS_PREFIX}:{worker_name}:{job_id}"

        metrics = {
            'worker_name': worker_name,
            'job_id': job_id,
            'status': WorkerStatus.RUNNING.value,
            'started_at': datetime.utcnow().isoformat()
        }

        self.redis.hset(metrics_key, mapping=metrics)
        self.redis.expire(metrics_key, self.METRICS_TTL)

        logger.info(f"Worker {worker_name} started (job: {job_id})")

        return metrics_key

    def record_completion(
        self,
        worker_name: str,
        job_id: str,
        status: WorkerStatus,
        duration: float,
        error_message: Optional[str] = None,
        result_summary: Optional[Dict[str, Any]] = None
    ):
        """
        Record worker completion

        Args:
            worker_name: Name of the worker
            job_id: Unique job ID
            status: Completion status
            duration: Execution duration in seconds
            error_message: Error message if failed
            result_summary: Summary of results
        """
        metrics_key = f"{self.METRICS_PREFIX}:{worker_name}:{job_id}"

        # Update metrics
        updates = {
            'status': status.value,
            'completed_at': datetime.utcnow().isoformat(),
            'duration': duration
        }

        if error_message:
            updates['error_message'] = error_message

        if result_summary:
            import json
            updates['result_summary'] = json.dumps(result_summary)

        self.redis.hset(metrics_key, mapping=updates)

        # Update statistics
        self._update_stats(worker_name, status, duration)

        # Add to history
        self._add_to_history(worker_name, job_id, status, duration)

        logger.info(
            f"Worker {worker_name} completed (job: {job_id}, "
            f"status: {status.value}, duration: {duration:.2f}s)"
        )

    def _update_stats(self, worker_name: str, status: WorkerStatus, duration: float):
        """
        Update worker statistics

        Args:
            worker_name: Name of the worker
            status: Execution status
            duration: Execution duration
        """
        stats_key = f"{self.STATS_PREFIX}:{worker_name}"

        # Increment counters
        self.redis.hincrby(stats_key, 'total_executions', 1)

        if status == WorkerStatus.SUCCESS:
            self.redis.hincrby(stats_key, 'successful_executions', 1)
        elif status == WorkerStatus.FAILED:
            self.redis.hincrby(stats_key, 'failed_executions', 1)

        # Update duration stats
        self.redis.hincrbyfloat(stats_key, 'total_duration', duration)

        # Update last execution
        self.redis.hset(stats_key, 'last_execution', datetime.utcnow().isoformat())
        self.redis.hset(stats_key, 'last_status', status.value)

        # Set expiry
        self.redis.expire(stats_key, self.METRICS_TTL)

    def _add_to_history(
        self,
        worker_name: str,
        job_id: str,
        status: WorkerStatus,
        duration: float
    ):
        """
        Add execution to history

        Args:
            worker_name: Name of the worker
            job_id: Job ID
            status: Execution status
            duration: Execution duration
        """
        history_key = f"{self.HISTORY_PREFIX}:{worker_name}"

        history_entry = {
            'job_id': job_id,
            'status': status.value,
            'duration': duration,
            'timestamp': datetime.utcnow().isoformat()
        }

        import json
        self.redis.lpush(history_key, json.dumps(history_entry))

        # Keep only last 100 executions
        self.redis.ltrim(history_key, 0, 99)

        # Set expiry
        self.redis.expire(history_key, self.METRICS_TTL)

    def get_worker_stats(self, worker_name: str) -> Dict[str, Any]:
        """
        Get worker statistics

        Args:
            worker_name: Name of the worker

        Returns:
            Worker statistics
        """
        stats_key = f"{self.STATS_PREFIX}:{worker_name}"

        stats = self.redis.hgetall(stats_key)

        if not stats:
            return {
                'worker_name': worker_name,
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'total_duration': 0.0,
                'average_duration': 0.0,
                'last_execution': None,
                'last_status': None
            }

        total_executions = int(stats.get('total_executions', 0))
        total_duration = float(stats.get('total_duration', 0))

        return {
            'worker_name': worker_name,
            'total_executions': total_executions,
            'successful_executions': int(stats.get('successful_executions', 0)),
            'failed_executions': int(stats.get('failed_executions', 0)),
            'total_duration': total_duration,
            'average_duration': total_duration / total_executions if total_executions > 0 else 0.0,
            'last_execution': stats.get('last_execution'),
            'last_status': stats.get('last_status')
        }

    def get_worker_history(
        self,
        worker_name: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get worker execution history

        Args:
            worker_name: Name of the worker
            limit: Maximum number of history entries

        Returns:
            List of history entries
        """
        history_key = f"{self.HISTORY_PREFIX}:{worker_name}"

        import json
        entries = self.redis.lrange(history_key, 0, limit - 1)

        return [json.loads(entry) for entry in entries]

    def get_all_worker_stats(self) -> List[Dict[str, Any]]:
        """
        Get statistics for all workers

        Returns:
            List of worker statistics
        """
        # Find all stats keys
        stats_keys = self.redis.keys(f"{self.STATS_PREFIX}:*")

        all_stats = []
        for stats_key in stats_keys:
            # Extract worker name from key
            worker_name = stats_key.replace(f"{self.STATS_PREFIX}:", "")
            stats = self.get_worker_stats(worker_name)
            all_stats.append(stats)

        return all_stats

    def get_recent_failures(
        self,
        limit: int = 10,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get recent failed worker executions

        Args:
            limit: Maximum number of failures to return
            hours: Look back period in hours

        Returns:
            List of recent failures
        """
        failures = []

        # Get all worker names
        stats_keys = self.redis.keys(f"{self.STATS_PREFIX}:*")

        for stats_key in stats_keys:
            worker_name = stats_key.replace(f"{self.STATS_PREFIX}:", "")
            history = self.get_worker_history(worker_name, limit=50)

            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            for entry in history:
                if entry['status'] == WorkerStatus.FAILED.value:
                    timestamp = datetime.fromisoformat(entry['timestamp'])
                    if timestamp >= cutoff_time:
                        failures.append({
                            'worker_name': worker_name,
                            **entry
                        })

        # Sort by timestamp (most recent first)
        failures.sort(key=lambda x: x['timestamp'], reverse=True)

        return failures[:limit]

    def clear_worker_stats(self, worker_name: str):
        """
        Clear statistics for a worker

        Args:
            worker_name: Name of the worker
        """
        stats_key = f"{self.STATS_PREFIX}:{worker_name}"
        history_key = f"{self.HISTORY_PREFIX}:{worker_name}"

        self.redis.delete(stats_key)
        self.redis.delete(history_key)

        logger.info(f"Cleared statistics for worker {worker_name}")

    def clear_all_stats(self):
        """Clear all worker statistics"""
        stats_keys = self.redis.keys(f"{self.STATS_PREFIX}:*")
        history_keys = self.redis.keys(f"{self.HISTORY_PREFIX}:*")

        for key in stats_keys + history_keys:
            self.redis.delete(key)

        logger.info("Cleared all worker statistics")


# Global monitor instance
_monitor_instance: Optional[WorkerMonitor] = None


def get_monitor() -> WorkerMonitor:
    """
    Get global monitor instance (singleton)

    Returns:
        WorkerMonitor instance
    """
    global _monitor_instance

    if _monitor_instance is None:
        _monitor_instance = WorkerMonitor()

    return _monitor_instance
