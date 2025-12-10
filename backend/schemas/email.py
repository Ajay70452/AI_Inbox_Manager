from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List, Optional


class EmailBase(BaseModel):
    """Base email schema"""

    sender: str
    recipients: List[str]
    body_text_clean: Optional[str] = None
    timestamp: datetime


class EmailCreate(EmailBase):
    """Email creation schema"""

    thread_id: UUID
    user_id: UUID
    email_id_provider: str
    body_html_url: Optional[str] = None


class EmailResponse(EmailBase):
    """Email response schema"""

    id: UUID
    thread_id: UUID
    email_id_provider: str
    body_html_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EmailSyncRequest(BaseModel):
    """Manual email sync request"""

    force: bool = False
