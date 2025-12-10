from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel


class CompanyContext(BaseModel):
    """Company context for AI processing"""

    __tablename__ = "company_context"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    tone = Column(Text)  # Tone guidelines
    company_description = Column(Text)
    products = Column(JSONB)  # List of products/services
    policies = Column(JSONB)  # Company policies
    faq = Column(JSONB)  # Frequently asked questions
    roles = Column(JSONB)  # Team roles and responsibilities
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="company_context")

    def __repr__(self):
        return f"<CompanyContext(id={self.id}, user_id={self.user_id})>"
