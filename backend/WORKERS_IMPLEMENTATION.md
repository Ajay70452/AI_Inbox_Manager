# Background Workers Implementation

This document describes the background worker system for AI Inbox Manager.

## Overview

The background worker system handles asynchronous tasks such as:
- Email synchronization from Gmail/Outlook
- AI processing of email threads
- Scheduled maintenance tasks

The system is built with:
- **APScheduler** for job scheduling
- **Redis** for monitoring and metrics storage
- **Worker Base Class** for standardized execution and error handling
- **CLI Commands** for worker management
- **REST API** for triggering and monitoring workers

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Scheduler (APScheduler)                   │ │
│  │  • Email Sync Job (every 5 minutes)                   │ │
│  │  • AI Processing Job (every 10 minutes)               │ │
│  │  • Nightly Cleanup Job (2 AM UTC)                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                             │                                │
│                             ▼                                │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    Workers                             │ │
│  │  • EmailSyncWorker                                     │ │
│  │  • BulkEmailSyncWorker                                │ │
│  │  • AIProcessingWorker                                  │ │
│  │  • BulkAIProcessingWorker                             │ │
│  └────────────────────────────────────────────────────────┘ │
│                             │                                │
│                             ▼                                │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           Worker Monitoring (Redis)                    │ │
│  │  • Execution metrics                                   │ │
│  │  • Statistics (success/failure counts)                │ │
│  │  • Execution history                                   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Base Worker (`workers/base.py`)

All workers inherit from `BaseWorker`, which provides:
- Standardized execution flow with `run()` method
- Error handling and logging
- Automatic monitoring integration
- Result summarization

**Usage:**
```python
from workers.base import BaseWorker

class MyWorker(BaseWorker):
    def __init__(self):
        super().__init__("my_worker")

    def execute(self, *args, **kwargs) -> Dict[str, Any]:
        # Implement worker logic here
        return {"result": "success"}

# Run the worker
worker = MyWorker()
result = worker.run(arg1, arg2)
```

**Return Format:**
```python
{
    "status": "success",  # or "failed"
    "worker": "worker_name",
    "job_id": "uuid-string",
    "duration": 1.23,  # seconds
    "result": {...},  # Worker-specific results
    "started_at": "2025-01-01T00:00:00",
    "completed_at": "2025-01-01T00:00:01"
}
```

### 2. Email Sync Workers (`workers/email_sync_worker.py`)

#### EmailSyncWorker
Syncs emails for a single user.

**Parameters:**
- `user_id` (str): User ID to sync
- `provider` (Optional[str]): 'gmail', 'outlook', or None for all
- `full_sync` (bool): If True, performs full sync
- `lookback_days` (Optional[int]): Days to look back for emails

**Example:**
```python
from workers.email_sync_worker import sync_user_emails

result = sync_user_emails(
    user_id="user-uuid",
    provider="gmail",
    full_sync=False,
    lookback_days=7
)
```

#### BulkEmailSyncWorker
Syncs emails for all users with connected accounts.

**Parameters:**
- `lookback_days` (Optional[int]): Days to look back

**Example:**
```python
from workers.email_sync_worker import sync_all_users

result = sync_all_users(lookback_days=7)
```

### 3. AI Processing Workers (`workers/ai_processing_worker.py`)

#### AIProcessingWorker
Processes a single thread with AI.

**Parameters:**
- `user_id` (str): User ID
- `thread_id` (str): Thread ID to process
- `tasks` (Optional[List[str]]): AI tasks to perform
  - Options: 'summarize', 'classify', 'sentiment', 'reply', 'tasks'
  - Default: All tasks

**Example:**
```python
from workers.ai_processing_worker import process_thread_ai

result = process_thread_ai(
    user_id="user-uuid",
    thread_id="thread-uuid",
    tasks=["summarize", "classify"]
)
```

#### BulkAIProcessingWorker
Processes multiple unprocessed threads.

**Parameters:**
- `user_id` (Optional[str]): Specific user or None for all users
- `limit` (int): Maximum threads to process
- `tasks` (Optional[List[str]]): AI tasks to perform

**Example:**
```python
from workers.ai_processing_worker import process_all_unprocessed_threads

result = process_all_unprocessed_threads(
    user_id=None,
    limit=50,
    tasks=None  # All tasks
)
```

### 4. Scheduler (`workers/scheduler.py`)

Manages periodic execution of workers using APScheduler.

**Features:**
- Automatic job scheduling on application startup
- Configurable intervals via settings
- Job pause/resume/remove functionality
- Event listeners for logging

**Jobs:**
1. **Email Sync Job**
   - Runs every `EMAIL_SYNC_INTERVAL_MINUTES` (default: 5 minutes)
   - Syncs emails for all users with connected accounts

2. **AI Processing Job**
   - Runs every `AI_PROCESSING_INTERVAL_MINUTES` (default: 10 minutes)
   - Processes up to `AI_PROCESSING_BATCH_SIZE` (default: 50) unprocessed threads

3. **Nightly Cleanup Job**
   - Runs at 2:00 AM UTC
   - Performs maintenance tasks (TODO: implement cleanup logic)

**Configuration:**
```python
# app/config.py
EMAIL_SYNC_INTERVAL_MINUTES = 5
EMAIL_SYNC_LOOKBACK_DAYS = 90
AI_PROCESSING_INTERVAL_MINUTES = 10
AI_PROCESSING_BATCH_SIZE = 50
```

### 5. Monitoring (`workers/monitoring.py`)

Tracks worker execution metrics in Redis.

**Features:**
- Real-time execution tracking
- Success/failure statistics
- Execution history (last 100 runs per worker)
- Recent failure reporting

**Metrics Tracked:**
- Total executions
- Successful executions
- Failed executions
- Total duration
- Average duration
- Last execution timestamp
- Last execution status

**Example:**
```python
from workers.monitoring import get_monitor

monitor = get_monitor()

# Get worker statistics
stats = monitor.get_worker_stats("email_sync")

# Get execution history
history = monitor.get_worker_history("email_sync", limit=20)

# Get recent failures
failures = monitor.get_recent_failures(limit=10, hours=24)
```

---

## CLI Commands

The CLI provides comprehensive worker management capabilities.

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Run CLI
python -m cli.main worker --help
```

### Available Commands

#### Scheduler Management
```bash
# Start scheduler (keeps running)
python -m cli.main worker scheduler start

# Show scheduler status
python -m cli.main worker scheduler status

# Pause a job
python -m cli.main worker scheduler pause email_sync_job

# Resume a job
python -m cli.main worker scheduler resume email_sync_job

# Remove a job
python -m cli.main worker scheduler remove email_sync_job
```

#### Email Sync
```bash
# Sync emails for a specific user
python -m cli.main worker sync user --user-id <user-id> --lookback-days 7

# Sync specific provider
python -m cli.main worker sync user --user-id <user-id> --provider gmail

# Full sync
python -m cli.main worker sync user --user-id <user-id> --full

# Sync all users
python -m cli.main worker sync all --lookback-days 7
```

#### AI Processing
```bash
# Process a specific thread
python -m cli.main worker ai thread --user-id <user-id> --thread-id <thread-id>

# Process with specific tasks
python -m cli.main worker ai thread --user-id <user-id> --thread-id <thread-id> --tasks summarize --tasks classify

# Bulk processing
python -m cli.main worker ai bulk --limit 50

# Bulk for specific user
python -m cli.main worker ai bulk --user-id <user-id> --limit 20
```

#### Monitoring
```bash
# Show all worker statistics
python -m cli.main worker monitor stats

# Show specific worker statistics
python -m cli.main worker monitor stats --worker-name email_sync

# Show execution history
python -m cli.main worker monitor history --worker-name email_sync --limit 20

# Show recent failures
python -m cli.main worker monitor failures --limit 10 --hours 24

# Clear worker statistics
python -m cli.main worker monitor clear --worker-name email_sync

# Clear all statistics
python -m cli.main worker monitor clear --all
```

---

## REST API Endpoints

### Trigger Workers

#### Trigger Email Sync
```http
POST /api/v1/workers/sync/trigger
Authorization: Bearer <token>
Content-Type: application/json

{
  "provider": "gmail",  // optional: "gmail", "outlook", or null for all
  "full_sync": false,
  "lookback_days": 7
}

Response:
{
  "success": true,
  "message": "Email sync completed successfully",
  "job_id": "uuid-string",
  "status": "success"
}
```

#### Trigger AI Processing
```http
POST /api/v1/workers/ai/process/trigger
Authorization: Bearer <token>
Content-Type: application/json

{
  "thread_id": "thread-uuid",
  "tasks": ["summarize", "classify"]  // optional
}

Response:
{
  "success": true,
  "message": "AI processing completed successfully",
  "job_id": "uuid-string",
  "status": "success"
}
```

### Scheduler Management

#### Get Scheduler Status
```http
GET /api/v1/workers/scheduler/status
Authorization: Bearer <token>

Response:
{
  "is_running": true,
  "jobs": [
    {
      "id": "email_sync_job",
      "name": "Email Sync for All Users",
      "next_run_time": "2025-01-01T00:05:00",
      "trigger": "interval[0:05:00]"
    }
  ]
}
```

#### Pause/Resume Job
```http
POST /api/v1/workers/scheduler/{job_id}/pause
POST /api/v1/workers/scheduler/{job_id}/resume
Authorization: Bearer <token>

Response:
{
  "success": true,
  "message": "Job 'email_sync_job' paused successfully"
}
```

### Monitoring

#### Get Worker Statistics
```http
GET /api/v1/workers/monitor/stats
GET /api/v1/workers/monitor/stats?worker_name=email_sync
Authorization: Bearer <token>

Response:
[
  {
    "worker_name": "email_sync",
    "total_executions": 100,
    "successful_executions": 98,
    "failed_executions": 2,
    "total_duration": 234.56,
    "average_duration": 2.35,
    "last_execution": "2025-01-01T00:00:00",
    "last_status": "success"
  }
]
```

#### Get Worker History
```http
GET /api/v1/workers/monitor/{worker_name}/history?limit=20
Authorization: Bearer <token>

Response:
{
  "worker_name": "email_sync",
  "history": [
    {
      "job_id": "uuid-string",
      "status": "success",
      "duration": 2.34,
      "timestamp": "2025-01-01T00:00:00"
    }
  ]
}
```

#### Get Recent Failures
```http
GET /api/v1/workers/monitor/failures?limit=10&hours=24
Authorization: Bearer <token>

Response:
{
  "failures": [
    {
      "worker_name": "ai_processing",
      "job_id": "uuid-string",
      "status": "failed",
      "duration": 5.67,
      "timestamp": "2025-01-01T00:00:00"
    }
  ],
  "period_hours": 24,
  "count": 1
}
```

---

## Configuration

### Environment Variables

```bash
# Redis
REDIS_URL=redis://localhost:6379/0

# Email Sync Settings
EMAIL_SYNC_INTERVAL_MINUTES=5
EMAIL_SYNC_LOOKBACK_DAYS=90

# AI Processing
AI_PROCESSING_INTERVAL_MINUTES=10
AI_PROCESSING_BATCH_SIZE=50
```

### Customizing Scheduler

To customize scheduled jobs, modify `workers/scheduler.py`:

```python
# Add custom job
scheduler.scheduler.add_job(
    func=my_custom_function,
    trigger=IntervalTrigger(hours=1),
    id='my_custom_job',
    name='My Custom Job'
)
```

---

## Monitoring & Troubleshooting

### Check Worker Status
```bash
# View all worker statistics
python -m cli.main worker monitor stats

# Check recent failures
python -m cli.main worker monitor failures
```

### Logs
Worker execution is logged to the application logger:
```
2025-01-01 00:00:00 - worker.email_sync - INFO - Starting worker: email_sync (job: uuid)
2025-01-01 00:00:02 - worker.email_sync - INFO - Worker email_sync completed successfully in 2.34s
```

### Redis Keys
Monitoring data is stored in Redis with the following keys:
- `worker:metrics:{worker_name}:{job_id}` - Execution metrics
- `worker:stats:{worker_name}` - Aggregated statistics
- `worker:history:{worker_name}` - Execution history (last 100)

---

## Best Practices

1. **Error Handling**: Workers should handle errors gracefully and return meaningful error messages

2. **Idempotency**: Workers should be idempotent where possible (safe to run multiple times)

3. **Timeouts**: Long-running workers should implement timeouts

4. **Rate Limiting**: Respect external API rate limits (Gmail, Outlook, LLM providers)

5. **Monitoring**: Regularly check worker statistics and recent failures

6. **Cleanup**: Periodically clear old monitoring data to prevent Redis bloat

---

## Future Enhancements

- [ ] Add webhook support for real-time email notifications
- [ ] Implement priority queues for urgent tasks
- [ ] Add worker health checks and automatic restart
- [ ] Implement distributed worker execution (Celery)
- [ ] Add alerting for worker failures (email/Slack)
- [ ] Implement rate limiting per worker
- [ ] Add worker performance metrics (CPU, memory)
- [ ] Create worker dashboard UI

---

## Testing

### Manual Testing
```bash
# Test email sync worker
python -m cli.main worker sync user --user-id <user-id> --lookback-days 1

# Test AI processing worker
python -m cli.main worker ai thread --user-id <user-id> --thread-id <thread-id> --tasks summarize

# Check results
python -m cli.main worker monitor stats
```

### Unit Tests
```python
# tests/test_workers.py
from workers.base import BaseWorker
from workers.monitoring import get_monitor

def test_worker_execution():
    worker = MyWorker()
    result = worker.run()
    assert result['status'] == 'success'

def test_monitoring():
    monitor = get_monitor()
    stats = monitor.get_worker_stats("test_worker")
    assert stats['total_executions'] > 0
```

---

## Support

For issues or questions:
1. Check worker logs
2. Review monitoring statistics
3. Check recent failures
4. Verify Redis connection
5. Ensure scheduler is running

---

**Last Updated:** 2025-11-26
**Version:** 1.0.0
