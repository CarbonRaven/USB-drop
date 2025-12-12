"""Deployment model - where USB drives are dropped."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Deployment(Base):
    """Record of where a USB drive was physically deployed."""

    __tablename__ = "deployments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drive_id = Column(UUID(as_uuid=True), ForeignKey("drives.id"), nullable=False, unique=True)

    # GPS coordinates
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)

    # Location description
    location_name = Column(String(255), nullable=True)
    location_description = Column(Text, nullable=True)
    location_type = Column(String(50), nullable=True)  # parking_lot, lobby, cafe, etc.

    # Address (if available)
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)

    # Photo evidence
    photo_url = Column(String(500), nullable=True)

    # Deployment info
    deployed_by = Column(String(100), nullable=True)
    deployment_notes = Column(Text, nullable=True)
    weather_conditions = Column(String(100), nullable=True)

    # Timestamps
    deployed_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    drive = relationship("Drive", back_populates="deployment")

    @property
    def coordinates(self) -> tuple | None:
        """Get coordinates as tuple."""
        if self.latitude and self.longitude:
            return (float(self.latitude), float(self.longitude))
        return None
