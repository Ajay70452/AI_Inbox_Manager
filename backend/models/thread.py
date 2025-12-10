from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Thread(BaseModel):
    """Email thread model"""

    __tablename__ = "threads"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    thread_id_provider = Column(String, nullable=False, index=True)  # Gmail/Outlook thread ID
    subject = Column(String, nullable=False)
    last_message_at = Column(DateTime, nullable=False)

    # Relationships
    user = relationship("User", back_populates="threads")
    emails = relationship("Email", back_populates="thread", cascade="all, delete-orphan")
    summary = relationship("AIThreadSummary", back_populates="thread", uselist=False, cascade="all, delete-orphan")
    priority = relationship("AIPriority", back_populates="thread", uselist=False, cascade="all, delete-orphan")
    sentiment = relationship("AISentiment", back_populates="thread", uselist=False, cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="thread", cascade="all, delete-orphan")
    reply_draft = relationship("AIReplyDraft", back_populates="thread", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Thread(id={self.id}, subject={self.subject[:50]})>"
