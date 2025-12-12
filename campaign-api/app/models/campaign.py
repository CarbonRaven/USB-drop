"""Campaign model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Date, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class CampaignStatus(str, enum.Enum):
    """Campaign status options."""
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Campaign(Base):
    """A USB drop campaign for a client."""

    __tablename__ = "campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    client_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    target_drive_count = Column(Integer, default=0)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(
        Enum(CampaignStatus),
        default=CampaignStatus.DRAFT,
        nullable=False
    )
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    drives = relationship("Drive", back_populates="campaign", cascade="all, delete-orphan")

    @property
    def drive_count(self) -> int:
        """Get actual number of drives in campaign."""
        return len(self.drives) if self.drives else 0

    @property
    def deployed_count(self) -> int:
        """Get number of deployed drives."""
        if not self.drives:
            return 0
        return sum(1 for d in self.drives if d.status in ["deployed", "triggered", "recovered"])

    @property
    def triggered_count(self) -> int:
        """Get number of triggered drives."""
        if not self.drives:
            return 0
        return sum(1 for d in self.drives if d.status in ["triggered"])
