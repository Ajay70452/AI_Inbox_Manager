from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List


class TaskBase(BaseModel):
    """Base task schema"""

    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    extracted_owner: Optional[str] = None
    status: str = "pending"


class TaskCreate(TaskBase):
    """Task creation schema"""

    thread_id: UUID


class TaskUpdate(BaseModel):
    """Task update schema"""

    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = None


class TaskResponse(TaskBase):
    """Task response schema"""

    id: UUID
    thread_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class TaskExtractionResponse(BaseModel):
    """Response from task extraction"""

    thread_id: UUID
    tasks: List[TaskResponse]
