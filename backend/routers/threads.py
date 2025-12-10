from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from db import get_db
from models import User, Thread, AIPriority, AISentiment, AccountToken
from schemas import ThreadListResponse, ThreadDetailResponse
from app.dependencies import get_current_user
from services.gmail_service import GmailService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


def get_thread_with_fallback(db: Session, user: User, thread_id: str) -> Optional[Thread]:
    """
    Get thread by ID with fallback strategies:
    1. Internal UUID
    2. Provider ID (exact match)
    3. Resolved Gmail ID (canonical hex)
    """
    try:
        # 1. Try UUID
        try:
            thread = db.query(Thread).filter(Thread.id == thread_id, Thread.user_id == user.id).first()
            if thread: return thread
        except Exception as e:
            # Not a valid UUID, rollback to clean transaction state
            logger.debug(f"Not a valid UUID: {thread_id}")
            db.rollback()

        # 2. Try Provider ID
        thread = db.query(Thread).filter(Thread.thread_id_provider == thread_id, Thread.user_id == user.id).first()
        if thread: return thread

        # 3. Try resolving Gmail ID
        # Check if user has Gmail
        has_gmail = db.query(AccountToken).filter(AccountToken.user_id == user.id, AccountToken.provider == 'gmail').first()
        if has_gmail:
            try:
                logger.info(f"Attempting to resolve Gmail ID: {thread_id}")
                service = GmailService(db, user)
                canonical_id = service.resolve_thread_id(thread_id)
                logger.info(f"Resolved to: {canonical_id}")
                if canonical_id:
                    # Try to find by canonical ID
                    thread = db.query(Thread).filter(Thread.thread_id_provider == canonical_id, Thread.user_id == user.id).first()
                    if thread: return thread

                    # If not found, maybe we need to sync it?
                    # But this function is just a getter. The caller should handle sync if needed.
            except Exception as e:
                logger.warning(f"Failed to resolve Gmail ID: {e}")
                db.rollback()

        return None
    except Exception as e:
        logger.error(f"Unexpected error in get_thread_with_fallback: {e}", exc_info=True)
        db.rollback()
        return None


@router.get("/", response_model=List[ThreadListResponse])
def list_threads(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    priority: Optional[str] = None,
    sentiment: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List email threads with filters

    Query parameters:
    - limit: Number of threads to return (default: 50, max: 100)
    - offset: Pagination offset (default: 0)
    - priority: Filter by priority level (urgent, customer, vendor, internal, low)
    - sentiment: Filter by sentiment (positive, neutral, negative)
    - search: Search in subject
    """
    query = db.query(Thread).filter(Thread.user_id == current_user.id)

    # Apply filters
    if priority:
        query = query.join(AIPriority).filter(AIPriority.priority_level == priority)

    if sentiment:
        query = query.join(AISentiment).filter(AISentiment.sentiment_label == sentiment)

    if search:
        query = query.filter(Thread.subject.ilike(f"%{search}%"))

    # Order and paginate
    threads = (
        query.order_by(Thread.last_message_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # TODO: Add email count, has_summary flags
    return threads


@router.get("/{thread_id}", response_model=ThreadDetailResponse)
def get_thread_detail(
    thread_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get detailed thread information including:
    - All emails in thread
    - AI summary
    - Priority classification
    - Sentiment analysis
    - Extracted tasks
    - Reply draft
    """
    thread = get_thread_with_fallback(db, current_user, thread_id)

    if not thread:
        # Return 404 instead of 200 with error dict
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Thread not found")

    return thread


@router.get("/{thread_id}/summary")
def get_thread_summary(
    thread_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(f"Fetching summary for thread_id: {thread_id}")
    thread = get_thread_with_fallback(db, current_user, thread_id)
        
    if not thread:
        logger.warning(f"Thread not found: {thread_id}")
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Thread not found")
        
    if not thread.summary:
        logger.warning(f"Summary not found for thread: {thread.id}")
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Summary not found")
        
    return thread.summary


@router.get("/{thread_id}/priority")
def get_thread_priority(
    thread_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    thread = get_thread_with_fallback(db, current_user, thread_id)
        
    if not thread:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Thread not found")
        
    if not thread.priority:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Priority not found")
        
    return thread.priority


@router.get("/{thread_id}/sentiment")
def get_thread_sentiment(
    thread_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    thread = get_thread_with_fallback(db, current_user, thread_id)
        
    if not thread:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Thread not found")
        
    if not thread.sentiment:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Sentiment not found")
        
    return thread.sentiment


@router.get("/{thread_id}/reply")
def get_thread_reply(
    thread_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    thread = get_thread_with_fallback(db, current_user, thread_id)
        
    if not thread:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Thread not found")
        
    if not thread.reply_draft:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Reply draft not found")
        
    return thread.reply_draft


@router.get("/{thread_id}/tasks")
def get_thread_tasks(
    thread_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    thread = get_thread_with_fallback(db, current_user, thread_id)
        
    if not thread:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Thread not found")
        
    return thread.tasks
