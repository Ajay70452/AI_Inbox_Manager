from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from db import get_db
from models import User, Thread
from schemas import (
    AIProcessRequest,
    AISummaryResponse,
    AIPriorityResponse,
    AISentimentResponse,
    AIReplyDraftResponse,
    AIReplyRegenerateRequest,
    TaskExtractionResponse,
    TaskResponse,
)
from app.dependencies import get_current_user
from services import (
    SummarizationService,
    ClassificationService,
    SentimentAnalysisService,
    ReplyGenerationService,
    TaskExtractionService,
)
from core import NotFoundError, ExternalServiceError
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/summarize", response_model=AISummaryResponse)
def summarize_thread(
    request: AIProcessRequest,
    force: bool = Query(False, description="Force regeneration even if summary exists"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate AI summary for email thread

    This will:
    1. Fetch thread and all emails
    2. Send to AI orchestration layer with company context
    3. Store and return summary

    The AI will generate a concise 2-3 sentence summary of the thread.
    """
    try:
        service = SummarizationService(db, current_user)
        summary = service.summarize_thread(
            thread_id=str(request.thread_id),
            force_regenerate=force
        )
        return summary
    except ValueError as e:
        raise NotFoundError(str(e))
    except Exception as e:
        logger.error(f"Summarization error: {str(e)}", exc_info=True)
        raise ExternalServiceError(f"Failed to generate summary: {str(e)}")


@router.post("/classify", response_model=AIPriorityResponse)
def classify_priority(
    request: AIProcessRequest,
    force: bool = Query(False, description="Force reclassification"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Classify email thread priority

    Returns priority level and category:
    - Priority levels: urgent, customer, vendor, internal, low
    - Category: Brief description of the email type

    Uses company context to better understand priorities.
    """
    try:
        service = ClassificationService(db, current_user)
        priority = service.classify_thread(
            thread_id=str(request.thread_id),
            force_regenerate=force
        )
        return priority
    except ValueError as e:
        raise NotFoundError(str(e))
    except Exception as e:
        logger.error(f"Classification error: {str(e)}", exc_info=True)
        raise ExternalServiceError(f"Failed to classify priority: {str(e)}")


@router.post("/sentiment", response_model=AISentimentResponse)
def analyze_sentiment(
    request: AIProcessRequest,
    force: bool = Query(False, description="Force re-analysis"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Analyze sentiment of email thread

    Returns:
    - sentiment_score: Float from -1.0 (very negative) to 1.0 (very positive)
    - sentiment_label: positive, neutral, or negative
    - anger_level: Float from 0.0 (calm) to 1.0 (very angry)
    - urgency_score: Float from 0.0 (not urgent) to 1.0 (extremely urgent)

    Useful for detecting frustrated customers and escalating appropriately.
    """
    try:
        service = SentimentAnalysisService(db, current_user)
        sentiment = service.analyze_thread(
            thread_id=str(request.thread_id),
            force_regenerate=force
        )
        return sentiment
    except ValueError as e:
        raise NotFoundError(str(e))
    except Exception as e:
        logger.error(f"Sentiment analysis error: {str(e)}", exc_info=True)
        raise ExternalServiceError(f"Failed to analyze sentiment: {str(e)}")


@router.post("/reply", response_model=AIReplyDraftResponse)
def generate_reply(
    request: AIProcessRequest,
    tone: Optional[str] = Query(None, description="Desired tone (overrides company context)"),
    force: bool = Query(False, description="Force regeneration"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate AI reply draft

    Uses:
    - Thread conversation history
    - Company context (policies, FAQs, tone guidelines)
    - User's specified tone preferences

    The draft is ready to review and send - NO automatic sending!
    """
    try:
        service = ReplyGenerationService(db, current_user)
        draft = service.generate_reply(
            thread_id=str(request.thread_id),
            tone=tone,
            force_regenerate=force
        )
        return draft
    except ValueError as e:
        raise NotFoundError(str(e))
    except Exception as e:
        logger.error(f"Reply generation error: {str(e)}", exc_info=True)
        raise ExternalServiceError(f"Failed to generate reply: {str(e)}")


@router.post("/reply/regenerate", response_model=AIReplyDraftResponse)
def regenerate_reply(
    request: AIReplyRegenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Regenerate reply with different style

    Rewrite options:
    - "shorter" - Make it more concise
    - "longer" - Add more detail
    - "more formal" - Professional tone
    - "friendlier" - Casual, warm tone
    - "more empathetic" - Show more understanding
    """
    try:
        service = ReplyGenerationService(db, current_user)
        draft = service.regenerate_with_style(
            thread_id=str(request.thread_id),
            style=request.tone
        )
        return draft
    except ValueError as e:
        raise NotFoundError(str(e))
    except Exception as e:
        logger.error(f"Reply regeneration error: {str(e)}", exc_info=True)
        raise ExternalServiceError(f"Failed to regenerate reply: {str(e)}")


@router.post("/tasks/extract", response_model=TaskExtractionResponse)
def extract_tasks(
    request: AIProcessRequest,
    force: bool = Query(False, description="Force re-extraction"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Extract tasks from email thread

    Returns list of action items with:
    - Title: Brief task description
    - Description: Detailed explanation
    - Due date: Extracted deadline (if mentioned)
    - Assigned owner: Person/role responsible (if identifiable)
    - Priority: high, medium, or low

    Only extracts explicit action items - doesn't hallucinate tasks.
    """
    try:
        service = TaskExtractionService(db, current_user)
        tasks = service.extract_tasks(
            thread_id=str(request.thread_id),
            force_regenerate=force
        )
        return TaskExtractionResponse(
            thread_id=request.thread_id,
            tasks=[TaskResponse.from_orm(task) for task in tasks]
        )
    except ValueError as e:
        raise NotFoundError(str(e))
    except Exception as e:
        logger.error(f"Task extraction error: {str(e)}", exc_info=True)
        raise ExternalServiceError(f"Failed to extract tasks: {str(e)}")
