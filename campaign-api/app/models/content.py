"""Generated Content model - AI-created files."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class GeneratedContent(Base):
    """AI-generated content (documents, images) for profiles."""

    __tablename__ = "generated_content"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)

    # Content type
    content_type = Column(String(50), nullable=False)  # document, image, pdf, text

    # Generation details
    prompt = Column(Text, nullable=True)
    model_used = Column(String(100), nullable=True)  # gpt-4, dall-e-3, etc.

    # File info
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)

    # Metadata
    metadata = Column(JSONB, default=dict)

    # Generation stats
    tokens_used = Column(Integer, nullable=True)
    generation_time_ms = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    profile = relationship("Profile", back_populates="generated_content")


# Example metadata JSONB:
# {
#     "document_type": "salary_report",
#     "ai_model": "gpt-4-turbo",
#     "generation_params": {
#         "temperature": 0.7,
#         "max_tokens": 2000
#     },
#     "image_params": {
#         "size": "1024x1024",
#         "quality": "standard",
#         "style": "natural"
#     }
# }
