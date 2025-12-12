"""Profile model - USB drive templates."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from app.database import Base


class Profile(Base):
    """USB drive profile template."""

    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Scenario categorization
    scenario_type = Column(String(50), nullable=False)  # hr, it, executive, creator, etc.
    theme = Column(String(50), nullable=True)

    # Template configuration (JSON)
    file_structure = Column(JSONB, default=dict)  # Files/folders to create
    token_config = Column(JSONB, default=dict)    # Token types and placement
    ai_prompts = Column(JSONB, default=dict)      # Prompts for AI content generation

    # Suggested USB drive labels
    label_suggestions = Column(ARRAY(String), default=list)

    # Metadata
    is_system = Column(String(10), default="false")  # Built-in vs user-created
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    drives = relationship("Drive", back_populates="profile")
    generated_content = relationship("GeneratedContent", back_populates="profile")


# Example file_structure JSONB:
# {
#     "folders": ["HR Documents", "Payroll", "Benefits"],
#     "files": [
#         {"name": "Employee_Salaries_2024.xlsx", "type": "excel_token", "folder": "Payroll"},
#         {"name": "Benefits_Overview.docx", "type": "word_token", "folder": "Benefits"},
#         {"name": "HR_Contacts.pdf", "type": "pdf_token", "folder": "HR Documents"},
#         {"name": "desktop.ini", "type": "folder_token", "folder": "HR Documents"}
#     ]
# }

# Example token_config JSONB:
# {
#     "tokens": [
#         {"type": "doc-msword", "count": 2, "redirect_theme": "corporate"},
#         {"type": "doc-msexcel", "count": 1, "redirect_theme": "login"},
#         {"type": "windows-dir", "count": 1},
#         {"type": "qr-code", "count": 1, "filename": "WiFi_Password.png"}
#     ]
# }

# Example ai_prompts JSONB:
# {
#     "document_content": "Create a professional HR document about employee benefits...",
#     "image_prompt": "Corporate office setting, professional environment, business casual..."
# }
