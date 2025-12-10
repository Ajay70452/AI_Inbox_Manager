from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class SyncJobLog(BaseModel):
    """Email sync job logs"""

    __tablename__ = "sync_job_logs"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    provider = Column(String, nullable=False)  # gmail or outlook
    status = Column(String, nullable=False)  # success, error
    run_time_ms = Column(Integer)
    message = Column(Text)

    # Relationships
    user = relationship("User", back_populates="sync_job_logs")

    def __repr__(self):
        return f"<SyncJobLog(id={self.id}, provider={self.provider}, status={self.status})>"
