"""
Workers API Router

Endpoints for managing and monitoring background workers
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List
from pydantic import BaseModel

from core.security import get_current_user
from models import User
from workers import get_scheduler
from workers.monitoring import get_monitor
from workers.email_sync_worker import sync_user_emails
from workers.ai_processing_worker import process_thread_ai

router = APIRouter()


# Request/Response Schemas

class WorkerJobRequest(BaseModel):
    """Request to trigger a worker job"""
    pass


class EmailSyncJobRequest(WorkerJobRequest):
    """Request to trigger email sync"""
    provider: Optional[str] = None
    full_sync: bool = False
    lookback_days: int = 7


class AIProcessingJobRequest(WorkerJobRequest):
    """Request to trigger AI processing"""
    thread_id: str
    tasks: Optional[List[str]] = None


class JobResponse(BaseModel):
    """Response for job trigger"""
    success: bool
    message: str
    job_id: str
    status: str


class SchedulerStatusResponse(BaseModel):
    """Scheduler status response"""
    is_running: bool
    jobs: List[dict]


class WorkerStatsResponse(BaseModel):
    """Worker statistics response"""
    worker_name: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    total_duration: float
    average_duration: float
    last_execution: Optional[str]
    last_status: Optional[str]


# Worker Job Endpoints

@router.post("/sync/trigger", response_model=JobResponse)
def trigger_email_sync_job(
    request: EmailSyncJobRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Trigger email sync job for current user

    This endpoint immediately executes an email sync job
    """
    try:
        result = sync_user_emails(
            user_id=str(current_user.id),
            provider=request.provider,
            full_sync=request.full_sync,
            lookback_days=request.lookback_days
        )

        if result['status'] == 'success':
            return JobResponse(
                success=True,
                message="Email sync completed successfully",
                job_id=result['job_id'],
                status=result['status']
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Email sync failed: {result.get('error')}"
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger email sync: {str(e)}"
        )


@router.post("/ai/process/trigger", response_model=JobResponse)
def trigger_ai_processing_job(
    request: AIProcessingJobRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Trigger AI processing job for a specific thread

    This endpoint immediately processes a thread with AI
    """
    try:
        result = process_thread_ai(
            user_id=str(current_user.id),
            thread_id=request.thread_id,
            tasks=request.tasks
        )

        if result['status'] == 'success':
            return JobResponse(
                success=True,
                message="AI processing completed successfully",
                job_id=result['job_id'],
                status=result['status']
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"AI processing failed: {result.get('error')}"
            )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger AI processing: {str(e)}"
        )


# Scheduler Management Endpoints

@router.get("/scheduler/status", response_model=SchedulerStatusResponse)
def get_scheduler_status(current_user: User = Depends(get_current_user)):
    """
    Get scheduler status and scheduled jobs

    Requires admin privileges (TODO: Add admin check)
    """
    try:
        scheduler = get_scheduler()

        return SchedulerStatusResponse(
            is_running=scheduler.is_running,
            jobs=scheduler.get_jobs_info()
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get scheduler status: {str(e)}"
        )


@router.post("/scheduler/{job_id}/pause")
def pause_scheduled_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Pause a scheduled job

    Requires admin privileges (TODO: Add admin check)
    """
    try:
        scheduler = get_scheduler()
        scheduler.pause_job(job_id)

        return {
            "success": True,
            "message": f"Job '{job_id}' paused successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to pause job: {str(e)}"
        )


@router.post("/scheduler/{job_id}/resume")
def resume_scheduled_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Resume a paused job

    Requires admin privileges (TODO: Add admin check)
    """
    try:
        scheduler = get_scheduler()
        scheduler.resume_job(job_id)

        return {
            "success": True,
            "message": f"Job '{job_id}' resumed successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resume job: {str(e)}"
        )


# Monitoring Endpoints

@router.get("/monitor/stats", response_model=List[WorkerStatsResponse])
def get_all_worker_stats(
    worker_name: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """
    Get worker statistics

    If worker_name is provided, returns stats for that worker only.
    Otherwise, returns stats for all workers.
    """
    try:
        monitor = get_monitor()

        if worker_name:
            stats = monitor.get_worker_stats(worker_name)
            return [WorkerStatsResponse(**stats)]
        else:
            all_stats = monitor.get_all_worker_stats()
            return [WorkerStatsResponse(**stats) for stats in all_stats]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get worker stats: {str(e)}"
        )


@router.get("/monitor/{worker_name}/history")
def get_worker_history(
    worker_name: str,
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """
    Get execution history for a worker
    """
    try:
        monitor = get_monitor()
        history = monitor.get_worker_history(worker_name, limit)

        return {
            "worker_name": worker_name,
            "history": history
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get worker history: {str(e)}"
        )


@router.get("/monitor/failures")
def get_recent_failures(
    limit: int = Query(10, ge=1, le=50),
    hours: int = Query(24, ge=1, le=168),
    current_user: User = Depends(get_current_user)
):
    """
    Get recent worker failures

    Args:
        limit: Maximum number of failures to return
        hours: Look back period in hours
    """
    try:
        monitor = get_monitor()
        failures = monitor.get_recent_failures(limit, hours)

        return {
            "failures": failures,
            "period_hours": hours,
            "count": len(failures)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recent failures: {str(e)}"
        )


@router.delete("/monitor/{worker_name}/stats")
def clear_worker_stats(
    worker_name: str,
    current_user: User = Depends(get_current_user)
):
    """
    Clear statistics for a worker

    Requires admin privileges (TODO: Add admin check)
    """
    try:
        monitor = get_monitor()
        monitor.clear_worker_stats(worker_name)

        return {
            "success": True,
            "message": f"Statistics cleared for worker '{worker_name}'"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear worker stats: {str(e)}"
        )
