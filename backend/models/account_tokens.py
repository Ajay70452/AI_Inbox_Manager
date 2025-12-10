from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class AccountToken(BaseModel):
    """OAuth tokens for Gmail/Outlook"""

    __tablename__ = "account_tokens"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    provider = Column(String, nullable=False)  # gmail or outlook
    email_address = Column(String, nullable=False)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)  # encrypted
    expires_at = Column(DateTime, nullable=False)

    # Relationships
    user = relationship("User", back_populates="account_tokens")

    def __repr__(self):
        return f"<AccountToken(id={self.id}, provider={self.provider}, email={self.email_address})>"
