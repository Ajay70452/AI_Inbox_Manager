from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Task(BaseModel):
    """Extracted task from email"""

    __tablename__ = "tasks"

    thread_id = Column(UUID(as_uuid=True), ForeignKey("threads.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    due_date = Column(DateTime)
    extracted_owner = Column(String)  # Role/person extracted from email
    status = Column(String, default="pending")  # pending, completed, cancelled

    # Relationships
    thread = relationship("Thread", back_populates="tasks")

    def __repr__(self):
        return f"<Task(id={self.id}, title={self.title[:50]})>"
