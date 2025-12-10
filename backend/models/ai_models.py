from sqlalchemy import Column, String, Text, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class AIThreadSummary(BaseModel):
    """AI-generated thread summary"""

    __tablename__ = "ai_thread_summary"

    thread_id = Column(UUID(as_uuid=True), ForeignKey("threads.id"), nullable=False, unique=True, index=True)
    summary_text = Column(Text, nullable=False)
    model_used = Column(String, nullable=False)

    # Relationships
    thread = relationship("Thread", back_populates="summary")

    def __repr__(self):
        return f"<AIThreadSummary(id={self.id}, thread_id={self.thread_id})>"


class AIPriority(BaseModel):
    """AI-generated priority classification"""

    __tablename__ = "ai_priority"

    thread_id = Column(UUID(as_uuid=True), ForeignKey("threads.id"), nullable=False, unique=True, index=True)
    priority_level = Column(String, nullable=False)  # urgent, customer, vendor, internal, low
    category = Column(String, nullable=False)

    # Relationships
    thread = relationship("Thread", back_populates="priority")

    def __repr__(self):
        return f"<AIPriority(id={self.id}, priority={self.priority_level})>"


class AISentiment(BaseModel):
    """AI-generated sentiment analysis"""

    __tablename__ = "ai_sentiment"

    thread_id = Column(UUID(as_uuid=True), ForeignKey("threads.id"), nullable=False, unique=True, index=True)
    sentiment_score = Column(Float, nullable=False)  # -1.0 to 1.0
    sentiment_label = Column(String, nullable=False)  # positive, neutral, negative
    anger_level = Column(Float, nullable=False)  # 0.0 to 1.0
    urgency_score = Column(Float, nullable=False)  # 0.0 to 1.0

    # Relationships
    thread = relationship("Thread", back_populates="sentiment")

    def __repr__(self):
        return f"<AISentiment(id={self.id}, sentiment={self.sentiment_label})>"


class AIReplyDraft(BaseModel):
    """AI-generated reply draft"""

    __tablename__ = "ai_reply_draft"

    thread_id = Column(UUID(as_uuid=True), ForeignKey("threads.id"), nullable=False, unique=True, index=True)
    draft_text = Column(Text, nullable=False)
    tone_used = Column(String, nullable=False)

    # Relationships
    thread = relationship("Thread", back_populates="reply_draft")

    def __repr__(self):
        return f"<AIReplyDraft(id={self.id}, thread_id={self.thread_id})>"
