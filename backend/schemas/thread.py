from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from .email import EmailResponse
from .ai import AISummaryResponse, AIPriorityResponse, AISentimentResponse, AIReplyDraftResponse
from .task import TaskResponse


class ThreadBase(BaseModel):
    """Base thread schema"""

    subject: str
    thread_id_provider: str
    last_message_at: datetime


class ThreadCreate(ThreadBase):
    """Thread creation schema"""

    user_id: UUID


class ThreadListResponse(BaseModel):
    """Thread list item response"""

    id: UUID
    subject: str
    last_message_at: datetime
    priority: Optional[str] = None
    sentiment_label: Optional[str] = None
    has_summary: bool = False
    email_count: int = 0

    class Config:
        from_attributes = True


class ThreadDetailResponse(ThreadBase):
    """Detailed thread response with all related data"""

    id: UUID
    created_at: datetime
    emails: List[EmailResponse] = []
    summary: Optional[AISummaryResponse] = None
    priority: Optional[AIPriorityResponse] = None
    sentiment: Optional[AISentimentResponse] = None
    tasks: List[TaskResponse] = []
    reply_draft: Optional[AIReplyDraftResponse] = None

    class Config:
        from_attributes = True


class ThreadQueryParams(BaseModel):
    """Thread query parameters"""

    limit: int = 50
    offset: int = 0
    priority: Optional[str] = None
    sentiment: Optional[str] = None
    search: Optional[str] = None
