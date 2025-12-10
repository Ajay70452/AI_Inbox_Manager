"""
Worker Management CLI Commands

Command-line interface for managing background workers
"""

import click
import logging
from typing import Optional

from workers import get_scheduler
from workers.email_sync_worker import sync_user_emails, sync_all_users
from workers.ai_processing_worker import process_thread_ai, process_all_unprocessed_threads
from workers.monitoring import get_monitor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@click.group()
def worker():
    """Worker management commands"""
    pass


@worker.group()
def scheduler():
    """Scheduler management commands"""
    pass


@scheduler.command()
def start():
    """Start the worker scheduler"""
    try:
        from workers import start_scheduler
        start_scheduler()
        click.echo("✓ Worker scheduler started successfully")

        # Display scheduled jobs
        sched = get_scheduler()
        jobs = sched.get_jobs_info()

        click.echo(f"\nScheduled jobs ({len(jobs)}):")
        for job in jobs:
            click.echo(f"  • {job['name']} (ID: {job['id']})")
            click.echo(f"    Next run: {job['next_run_time']}")

        # Keep running
        click.echo("\nPress Ctrl+C to stop...")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            click.echo("\n\nStopping scheduler...")
            sched.stop()
            click.echo("✓ Worker scheduler stopped")

    except Exception as e:
        click.echo(f"✗ Failed to start scheduler: {e}", err=True)
        raise click.Abort()


@scheduler.command()
def stop():
    """Stop the worker scheduler"""
    try:
        from workers import stop_scheduler
        stop_scheduler()
        click.echo("✓ Worker scheduler stopped successfully")
    except Exception as e:
        click.echo(f"✗ Failed to stop scheduler: {e}", err=True)
        raise click.Abort()


@scheduler.command()
def status():
    """Show scheduler status and jobs"""
    try:
        sched = get_scheduler()

        if sched.is_running:
            click.echo("Scheduler status: Running ✓")
        else:
            click.echo("Scheduler status: Stopped ✗")

        # Display scheduled jobs
        jobs = sched.get_jobs_info()

        if not jobs:
            click.echo("\nNo scheduled jobs")
            return

        click.echo(f"\nScheduled jobs ({len(jobs)}):")
        for job in jobs:
            click.echo(f"\n  • {job['name']}")
            click.echo(f"    ID: {job['id']}")
            click.echo(f"    Next run: {job['next_run_time']}")
            click.echo(f"    Trigger: {job['trigger']}")

    except Exception as e:
        click.echo(f"✗ Failed to get scheduler status: {e}", err=True)
        raise click.Abort()


@scheduler.command()
@click.argument('job_id')
def pause(job_id: str):
    """Pause a scheduled job"""
    try:
        sched = get_scheduler()
        sched.pause_job(job_id)
        click.echo(f"✓ Job '{job_id}' paused successfully")
    except Exception as e:
        click.echo(f"✗ Failed to pause job: {e}", err=True)
        raise click.Abort()


@scheduler.command()
@click.argument('job_id')
def resume(job_id: str):
    """Resume a paused job"""
    try:
        sched = get_scheduler()
        sched.resume_job(job_id)
        click.echo(f"✓ Job '{job_id}' resumed successfully")
    except Exception as e:
        click.echo(f"✗ Failed to resume job: {e}", err=True)
        raise click.Abort()


@scheduler.command()
@click.argument('job_id')
def remove(job_id: str):
    """Remove a scheduled job"""
    try:
        sched = get_scheduler()
        sched.remove_job(job_id)
        click.echo(f"✓ Job '{job_id}' removed successfully")
    except Exception as e:
        click.echo(f"✗ Failed to remove job: {e}", err=True)
        raise click.Abort()


@worker.group()
def sync():
    """Email sync worker commands"""
    pass


@sync.command()
@click.option('--user-id', required=True, help='User ID to sync')
@click.option('--provider', type=click.Choice(['gmail', 'outlook']), help='Specific provider')
@click.option('--full', is_flag=True, help='Perform full sync')
@click.option('--lookback-days', type=int, default=7, help='Days to look back')
def user(user_id: str, provider: Optional[str], full: bool, lookback_days: int):
    """Sync emails for a specific user"""
    try:
        click.echo(f"Starting email sync for user {user_id}...")

        result = sync_user_emails(
            user_id=user_id,
            provider=provider,
            full_sync=full,
            lookback_days=lookback_days
        )

        if result['status'] == 'success':
            stats = result['result']
            click.echo(f"\n✓ Sync completed successfully")
            click.echo(f"  Duration: {result['duration']:.2f}s")
            click.echo(f"  Emails: {stats.get('total_emails', 0)}")
            click.echo(f"  Threads: {stats.get('total_threads', 0)}")
        else:
            click.echo(f"\n✗ Sync failed: {result.get('error')}", err=True)

    except Exception as e:
        click.echo(f"✗ Failed to sync user emails: {e}", err=True)
        raise click.Abort()


@sync.command()
@click.option('--lookback-days', type=int, default=7, help='Days to look back')
def all(lookback_days: int):
    """Sync emails for all users"""
    try:
        click.echo("Starting bulk email sync for all users...")

        result = sync_all_users(lookback_days=lookback_days)

        if result['status'] == 'success':
            stats = result['result']
            click.echo(f"\n✓ Bulk sync completed")
            click.echo(f"  Duration: {result['duration']:.2f}s")
            click.echo(f"  Users synced: {stats.get('users_synced', 0)}")
            click.echo(f"  Users failed: {stats.get('users_failed', 0)}")
            click.echo(f"  Total emails: {stats.get('total_emails', 0)}")
            click.echo(f"  Total threads: {stats.get('total_threads', 0)}")

            if stats.get('errors'):
                click.echo(f"\n  Errors ({len(stats['errors'])}):")
                for error in stats['errors'][:5]:  # Show first 5 errors
                    click.echo(f"    - {error}")
        else:
            click.echo(f"\n✗ Bulk sync failed: {result.get('error')}", err=True)

    except Exception as e:
        click.echo(f"✗ Failed to sync all users: {e}", err=True)
        raise click.Abort()


@worker.group()
def ai():
    """AI processing worker commands"""
    pass


@ai.command()
@click.option('--user-id', required=True, help='User ID')
@click.option('--thread-id', required=True, help='Thread ID to process')
@click.option('--tasks', multiple=True, type=click.Choice(['summarize', 'classify', 'sentiment', 'reply', 'tasks']),
              help='Specific AI tasks to run')
def thread(user_id: str, thread_id: str, tasks: tuple):
    """Process a specific thread with AI"""
    try:
        task_list = list(tasks) if tasks else None

        click.echo(f"Starting AI processing for thread {thread_id}...")
        if task_list:
            click.echo(f"Tasks: {', '.join(task_list)}")

        result = process_thread_ai(
            user_id=user_id,
            thread_id=thread_id,
            tasks=task_list
        )

        if result['status'] == 'success':
            results = result['result']
            click.echo(f"\n✓ AI processing completed")
            click.echo(f"  Duration: {result['duration']:.2f}s")

            for task_name, task_result in results.items():
                if task_result.get('success'):
                    click.echo(f"  • {task_name}: ✓")
                else:
                    click.echo(f"  • {task_name}: ✗ ({task_result.get('error')})")
        else:
            click.echo(f"\n✗ AI processing failed: {result.get('error')}", err=True)

    except Exception as e:
        click.echo(f"✗ Failed to process thread: {e}", err=True)
        raise click.Abort()


@ai.command()
@click.option('--user-id', help='Specific user ID (optional)')
@click.option('--limit', type=int, default=50, help='Maximum threads to process')
@click.option('--tasks', multiple=True, type=click.Choice(['summarize', 'classify', 'sentiment', 'reply', 'tasks']),
              help='Specific AI tasks to run')
def bulk(user_id: Optional[str], limit: int, tasks: tuple):
    """Process unprocessed threads with AI"""
    try:
        task_list = list(tasks) if tasks else None

        click.echo(f"Starting bulk AI processing...")
        if user_id:
            click.echo(f"User: {user_id}")
        click.echo(f"Limit: {limit} threads")
        if task_list:
            click.echo(f"Tasks: {', '.join(task_list)}")

        result = process_all_unprocessed_threads(
            user_id=user_id,
            limit=limit,
            tasks=task_list
        )

        if result['status'] == 'success':
            stats = result['result']
            click.echo(f"\n✓ Bulk AI processing completed")
            click.echo(f"  Duration: {result['duration']:.2f}s")
            click.echo(f"  Threads processed: {stats.get('threads_processed', 0)}")
            click.echo(f"  Threads failed: {stats.get('threads_failed', 0)}")

            if stats.get('errors'):
                click.echo(f"\n  Errors ({len(stats['errors'])}):")
                for error in stats['errors'][:5]:  # Show first 5 errors
                    click.echo(f"    - {error}")
        else:
            click.echo(f"\n✗ Bulk AI processing failed: {result.get('error')}", err=True)

    except Exception as e:
        click.echo(f"✗ Failed to process threads: {e}", err=True)
        raise click.Abort()


@worker.group()
def monitor():
    """Worker monitoring commands"""
    pass


@monitor.command()
@click.option('--worker-name', help='Specific worker name')
def stats(worker_name: Optional[str]):
    """Show worker statistics"""
    try:
        mon = get_monitor()

        if worker_name:
            # Show stats for specific worker
            stats = mon.get_worker_stats(worker_name)

            click.echo(f"\nWorker: {stats['worker_name']}")
            click.echo(f"  Total executions: {stats['total_executions']}")
            click.echo(f"  Successful: {stats['successful_executions']} ✓")
            click.echo(f"  Failed: {stats['failed_executions']} ✗")
            click.echo(f"  Total duration: {stats['total_duration']:.2f}s")
            click.echo(f"  Average duration: {stats['average_duration']:.2f}s")
            click.echo(f"  Last execution: {stats['last_execution']}")
            click.echo(f"  Last status: {stats['last_status']}")

        else:
            # Show stats for all workers
            all_stats = mon.get_all_worker_stats()

            if not all_stats:
                click.echo("No worker statistics available")
                return

            click.echo(f"\nAll Workers ({len(all_stats)}):\n")

            for stats in all_stats:
                click.echo(f"  {stats['worker_name']}")
                click.echo(f"    Executions: {stats['total_executions']} "
                          f"(✓ {stats['successful_executions']}, "
                          f"✗ {stats['failed_executions']})")
                click.echo(f"    Avg duration: {stats['average_duration']:.2f}s")
                click.echo(f"    Last: {stats['last_execution']} ({stats['last_status']})")
                click.echo()

    except Exception as e:
        click.echo(f"✗ Failed to get worker stats: {e}", err=True)
        raise click.Abort()


@monitor.command()
@click.option('--worker-name', required=True, help='Worker name')
@click.option('--limit', type=int, default=20, help='Number of history entries')
def history(worker_name: str, limit: int):
    """Show worker execution history"""
    try:
        mon = get_monitor()
        hist = mon.get_worker_history(worker_name, limit)

        if not hist:
            click.echo(f"No history available for worker '{worker_name}'")
            return

        click.echo(f"\nExecution History for '{worker_name}' (last {len(hist)}):\n")

        for entry in hist:
            status_icon = "✓" if entry['status'] == 'success' else "✗"
            click.echo(f"  {status_icon} Job {entry['job_id']}")
            click.echo(f"    Status: {entry['status']}")
            click.echo(f"    Duration: {entry['duration']:.2f}s")
            click.echo(f"    Time: {entry['timestamp']}")
            click.echo()

    except Exception as e:
        click.echo(f"✗ Failed to get worker history: {e}", err=True)
        raise click.Abort()


@monitor.command()
@click.option('--limit', type=int, default=10, help='Number of failures to show')
@click.option('--hours', type=int, default=24, help='Look back period in hours')
def failures(limit: int, hours: int):
    """Show recent worker failures"""
    try:
        mon = get_monitor()
        recent_failures = mon.get_recent_failures(limit, hours)

        if not recent_failures:
            click.echo(f"✓ No failures in the last {hours} hours")
            return

        click.echo(f"\nRecent Failures (last {hours} hours):\n")

        for failure in recent_failures:
            click.echo(f"  ✗ {failure['worker_name']} - Job {failure['job_id']}")
            click.echo(f"    Duration: {failure['duration']:.2f}s")
            click.echo(f"    Time: {failure['timestamp']}")
            click.echo()

    except Exception as e:
        click.echo(f"✗ Failed to get recent failures: {e}", err=True)
        raise click.Abort()


@monitor.command()
@click.option('--worker-name', help='Clear stats for specific worker')
@click.option('--all', 'clear_all', is_flag=True, help='Clear all worker statistics')
@click.confirmation_option(prompt='Are you sure you want to clear statistics?')
def clear(worker_name: Optional[str], clear_all: bool):
    """Clear worker statistics"""
    try:
        mon = get_monitor()

        if clear_all:
            mon.clear_all_stats()
            click.echo("✓ Cleared all worker statistics")
        elif worker_name:
            mon.clear_worker_stats(worker_name)
            click.echo(f"✓ Cleared statistics for worker '{worker_name}'")
        else:
            click.echo("Specify --worker-name or --all", err=True)
            raise click.Abort()

    except Exception as e:
        click.echo(f"✗ Failed to clear statistics: {e}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    worker()
