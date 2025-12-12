"""Token model - CanaryTokens linked to drives."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Token(Base):
    """Individual Canarytoken associated with a drive."""

    __tablename__ = "tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drive_id = Column(UUID(as_uuid=True), ForeignKey("drives.id"), nullable=False)

    # CanaryTokens API data
    canary_token_id = Column(String(255), nullable=False, unique=True, index=True)
    token_type = Column(String(50), nullable=False)  # dns, doc-msword, doc-msexcel, etc.

    # File info
    filename = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=True)

    # Token metadata
    memo = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)  # Token URL/hostname
    redirect_url = Column(String(500), nullable=True)
    redirect_theme = Column(String(50), nullable=True)

    # AWS tokens
    aws_access_key_id = Column(String(50), nullable=True)
    aws_secret_access_key = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    first_triggered_at = Column(DateTime, nullable=True)
    last_triggered_at = Column(DateTime, nullable=True)

    # Relationships
    drive = relationship("Drive", back_populates="tokens")
    triggers = relationship("Trigger", back_populates="token", cascade="all, delete-orphan")

    @property
    def trigger_count(self) -> int:
        """Get number of times this token was triggered."""
        return len(self.triggers) if self.triggers else 0

    @property
    def is_triggered(self) -> bool:
        """Check if token has been triggered at least once."""
        return self.first_triggered_at is not None
