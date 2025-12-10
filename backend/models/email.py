from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import BaseModel


class Email(BaseModel):
    """Individual email model"""

    __tablename__ = "emails"

    thread_id = Column(UUID(as_uuid=True), ForeignKey("threads.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    email_id_provider = Column(String, nullable=False, unique=True, index=True)  # Gmail/Outlook email ID
    sender = Column(String, nullable=False)
    recipients = Column(JSONB, nullable=False)  # List of recipient emails
    body_html_url = Column(String)  # S3/R2 URL for HTML content
    body_text_clean = Column(Text)  # Clean text version
    timestamp = Column(DateTime, nullable=False, index=True)

    # Relationships
    thread = relationship("Thread", back_populates="emails")
    user = relationship("User", back_populates="emails")

    def __repr__(self):
        return f"<Email(id={self.id}, sender={self.sender}, timestamp={self.timestamp})>"
