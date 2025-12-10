from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any


class IntegrationBase(BaseModel):
    """Base integration schema"""

    type: str  # slack, notion, clickup, jira, trello
    workspace_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class IntegrationCreate(IntegrationBase):
    """Integration creation schema"""

    access_token: str
    refresh_token: Optional[str] = None


class IntegrationResponse(BaseModel):
    """Integration response schema (without tokens)"""

    id: UUID
    type: str
    workspace_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    is_active: bool = True

    class Config:
        from_attributes = True


class SlackAlertRequest(BaseModel):
    """Manual Slack alert request"""

    thread_id: UUID
    message: Optional[str] = None


class TaskIntegrationRequest(BaseModel):
    """Request to create task in external tool"""

    task_id: UUID
    integration_type: str  # notion, clickup, jira, trello
