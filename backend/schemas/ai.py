from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class AIProcessRequest(BaseModel):
    """Generic AI processing request"""

    thread_id: str


class AISummaryResponse(BaseModel):
    """AI summary response"""

    id: UUID
    thread_id: UUID
    summary_text: str
    model_used: str
    created_at: datetime

    class Config:
        from_attributes = True


class AIPriorityResponse(BaseModel):
    """AI priority classification response"""

    id: UUID
    thread_id: UUID
    priority_level: str  # urgent, customer, vendor, internal, low
    category: str
    created_at: datetime

    class Config:
        from_attributes = True


class AISentimentResponse(BaseModel):
    """AI sentiment analysis response"""

    id: UUID
    thread_id: UUID
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    sentiment_label: str  # positive, neutral, negative
    anger_level: float = Field(..., ge=0.0, le=1.0)
    urgency_score: float = Field(..., ge=0.0, le=1.0)
    created_at: datetime

    class Config:
        from_attributes = True


class AIReplyDraftResponse(BaseModel):
    """AI reply draft response"""

    id: UUID
    thread_id: UUID
    draft_text: str
    tone_used: str
    created_at: datetime

    class Config:
        from_attributes = True


class AIReplyRegenerateRequest(BaseModel):
    """Request to regenerate reply with different tone"""

    thread_id: UUID
    tone: str  # shorter, longer, formal, friendly, etc.
