"""Content generation router - OpenAI integration."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uuid

from app.database import get_db
from app.models.content import GeneratedContent
from app.models.profile import Profile
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.content_generator import ContentGenerator

router = APIRouter()


class DocumentRequest(BaseModel):
    prompt: str
    document_type: str = "general"  # general, salary, hr, financial, technical
    filename: str = "document.docx"
    profile_id: Optional[uuid.UUID] = None


class ImageRequest(BaseModel):
    prompt: str
    size: str = "1024x1024"
    style: str = "natural"  # natural or vivid
    filename: str = "image.png"
    profile_id: Optional[uuid.UUID] = None


class ContentResponse(BaseModel):
    id: uuid.UUID
    content_type: str
    filename: str
    file_path: str
    prompt: str

    class Config:
        from_attributes = True


class TemplateInfo(BaseModel):
    name: str
    description: str
    example_prompt: str
    document_type: str


@router.post("/document", response_model=ContentResponse)
async def generate_document(
    request: DocumentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a document using AI."""
    try:
        generator = ContentGenerator()
        content = await generator.generate_document(
            prompt=request.prompt,
            document_type=request.document_type,
            filename=request.filename,
            profile_id=request.profile_id,
            db=db,
        )
        return content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.post("/image", response_model=ContentResponse)
async def generate_image(
    request: ImageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate an image using DALL-E."""
    try:
        generator = ContentGenerator()
        content = await generator.generate_image(
            prompt=request.prompt,
            size=request.size,
            style=request.style,
            filename=request.filename,
            profile_id=request.profile_id,
            db=db,
        )
        return content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.get("/templates", response_model=list[TemplateInfo])
async def list_templates(
    current_user: User = Depends(get_current_user),
):
    """List available document templates."""
    return [
        TemplateInfo(
            name="Salary Report",
            description="Employee salary and compensation document",
            example_prompt="Create a confidential employee salary report for Q4 2024 showing compensation data for the engineering department.",
            document_type="salary",
        ),
        TemplateInfo(
            name="HR Policy",
            description="Human resources policy document",
            example_prompt="Create an HR policy document about remote work guidelines and expense reimbursement procedures.",
            document_type="hr",
        ),
        TemplateInfo(
            name="Financial Projection",
            description="Financial forecasting spreadsheet content",
            example_prompt="Create content for a financial projection showing revenue forecasts and budget allocations.",
            document_type="financial",
        ),
        TemplateInfo(
            name="Technical Documentation",
            description="Technical or IT documentation",
            example_prompt="Create AWS infrastructure documentation including server configurations and access credentials.",
            document_type="technical",
        ),
        TemplateInfo(
            name="Meeting Notes",
            description="Meeting minutes or notes",
            example_prompt="Create meeting notes from an executive strategy session discussing M&A targets.",
            document_type="general",
        ),
    ]


@router.post("/profile/{profile_id}/generate-all")
async def generate_profile_content(
    profile_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate all AI content for a profile's templates."""
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    ai_prompts = profile.ai_prompts or {}
    if not ai_prompts:
        raise HTTPException(status_code=400, detail="Profile has no AI prompts configured")

    generator = ContentGenerator()
    results = []

    try:
        # Generate documents
        for doc_prompt in ai_prompts.get("documents", []):
            content = await generator.generate_document(
                prompt=doc_prompt.get("prompt", ""),
                document_type=doc_prompt.get("type", "general"),
                filename=doc_prompt.get("filename", "document.docx"),
                profile_id=profile_id,
                db=db,
            )
            results.append({
                "type": "document",
                "filename": content.filename,
                "status": "success"
            })

        # Generate images
        for img_prompt in ai_prompts.get("images", []):
            content = await generator.generate_image(
                prompt=img_prompt.get("prompt", ""),
                size=img_prompt.get("size", "1024x1024"),
                style=img_prompt.get("style", "natural"),
                filename=img_prompt.get("filename", "image.png"),
                profile_id=profile_id,
                db=db,
            )
            results.append({
                "type": "image",
                "filename": content.filename,
                "status": "success"
            })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

    return {"profile_id": str(profile_id), "generated": results}
