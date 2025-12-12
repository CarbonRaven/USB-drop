"""Drive model - Individual USB drives."""

import uuid
import secrets
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class DriveStatus(str, enum.Enum):
    """Drive lifecycle status."""
    CREATED = "created"      # Record created, not yet prepared
    PREPARED = "prepared"    # Tokens generated, ready to write to USB
    DEPLOYED = "deployed"    # Physically placed in the field
    TRIGGERED = "triggered"  # At least one token has been triggered
    RECOVERED = "recovered"  # Drive was recovered/collected


def generate_drive_code() -> str:
    """Generate a unique drive code like USB-A1B2C3."""
    suffix = secrets.token_hex(3).upper()
    return f"USB-{suffix}"


class Drive(Base):
    """Individual USB drive instance."""

    __tablename__ = "drives"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)

    # Unique identifier
    unique_code = Column(String(20), unique=True, nullable=False, default=generate_drive_code)

    # Status tracking
    status = Column(Enum(DriveStatus), default=DriveStatus.CREATED, nullable=False)

    # Physical drive info
    label = Column(String(100), nullable=True)  # What's written on the drive
    drive_brand = Column(String(50), nullable=True)
    drive_capacity = Column(String(20), nullable=True)  # e.g., "8GB", "16GB"

    # Generated files manifest
    files_manifest = Column(JSONB, default=dict)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    prepared_at = Column(DateTime, nullable=True)
    deployed_at = Column(DateTime, nullable=True)
    triggered_at = Column(DateTime, nullable=True)
    recovered_at = Column(DateTime, nullable=True)

    # Relationships
    campaign = relationship("Campaign", back_populates="drives")
    profile = relationship("Profile", back_populates="drives")
    tokens = relationship("Token", back_populates="drive", cascade="all, delete-orphan")
    deployment = relationship("Deployment", back_populates="drive", uselist=False)

    @property
    def trigger_count(self) -> int:
        """Get total number of token triggers for this drive."""
        if not self.tokens:
            return 0
        return sum(len(t.triggers) for t in self.tokens if t.triggers)


# Example files_manifest JSONB:
# {
#     "files": [
#         {
#             "path": "HR Documents/Employee_Salaries_2024.xlsx",
#             "token_id": "abc123",
#             "size_bytes": 15234,
#             "created_at": "2024-01-15T10:30:00Z"
#         },
#         {
#             "path": "HR Documents/desktop.ini",
#             "token_id": "def456",
#             "size_bytes": 256,
#             "created_at": "2024-01-15T10:30:00Z"
#         }
#     ],
#     "total_size_bytes": 125890,
#     "file_count": 5
# }
