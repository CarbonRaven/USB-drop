"""Trigger model - Token activation events."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
from app.database import Base


class Trigger(Base):
    """Record of a token being triggered/activated."""

    __tablename__ = "triggers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token_id = Column(UUID(as_uuid=True), ForeignKey("tokens.id"), nullable=False)

    # Source information
    source_ip = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)

    # Geolocation (from IP)
    geo_city = Column(String(100), nullable=True)
    geo_region = Column(String(100), nullable=True)
    geo_country = Column(String(100), nullable=True)
    geo_country_code = Column(String(10), nullable=True)
    geo_latitude = Column(Numeric(10, 8), nullable=True)
    geo_longitude = Column(Numeric(11, 8), nullable=True)
    geo_isp = Column(String(255), nullable=True)
    geo_org = Column(String(255), nullable=True)

    # Additional data from CanaryTokens webhook
    additional_data = Column(JSONB, default=dict)

    # Raw webhook payload (for debugging)
    raw_payload = Column(JSONB, nullable=True)

    # Timestamps
    triggered_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    token = relationship("Token", back_populates="triggers")

    @property
    def coordinates(self) -> tuple | None:
        """Get geo coordinates as tuple."""
        if self.geo_latitude and self.geo_longitude:
            return (float(self.geo_latitude), float(self.geo_longitude))
        return None

    @property
    def location_summary(self) -> str:
        """Get human-readable location summary."""
        parts = []
        if self.geo_city:
            parts.append(self.geo_city)
        if self.geo_region:
            parts.append(self.geo_region)
        if self.geo_country:
            parts.append(self.geo_country)
        return ", ".join(parts) if parts else "Unknown location"
