from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import BaseModel


class Integration(BaseModel):
    """Third-party integrations (Slack, ClickUp, Notion, etc.)"""

    __tablename__ = "integrations"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String, nullable=False)  # slack, notion, clickup, jira, trello
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text)
    workspace_id = Column(String)  # Slack workspace, Notion workspace, etc.
    extra_data = Column(JSONB)  # Additional integration-specific data

    # Relationships
    user = relationship("User", back_populates="integrations")

    def __repr__(self):
        return f"<Integration(id={self.id}, type={self.type})>"
