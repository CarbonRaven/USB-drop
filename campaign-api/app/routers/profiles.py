"""Profiles router - USB drive templates."""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uuid

from app.database import get_db
from app.models.profile import Profile
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter()


# Pydantic models
class ProfileCreate(BaseModel):
    name: str
    description: Optional[str] = None
    scenario_type: str  # hr, it, executive, creator, etc.
    theme: Optional[str] = None
    file_structure: dict = {}
    token_config: dict = {}
    ai_prompts: dict = {}
    label_suggestions: List[str] = []


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    scenario_type: Optional[str] = None
    theme: Optional[str] = None
    file_structure: Optional[dict] = None
    token_config: Optional[dict] = None
    ai_prompts: Optional[dict] = None
    label_suggestions: Optional[List[str]] = None


class ProfileResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    scenario_type: str
    theme: Optional[str]
    file_structure: dict
    token_config: dict
    ai_prompts: dict
    label_suggestions: List[str]
    is_system: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FilePreview(BaseModel):
    path: str
    type: str
    token_type: Optional[str] = None


class ProfilePreview(BaseModel):
    profile_id: uuid.UUID
    files: List[FilePreview]
    token_summary: dict


@router.get("", response_model=List[ProfileResponse])
async def list_profiles(
    scenario_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all profiles."""
    query = db.query(Profile)
    if scenario_type:
        query = query.filter(Profile.scenario_type == scenario_type)
    profiles = query.order_by(Profile.name).all()
    return profiles


@router.post("", response_model=ProfileResponse)
async def create_profile(
    profile_data: ProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new profile."""
    profile = Profile(**profile_data.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get profile by ID."""
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/{profile_id}", response_model=ProfileResponse)
async def update_profile(
    profile_id: uuid.UUID,
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a profile."""
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if profile.is_system == "true":
        raise HTTPException(status_code=400, detail="Cannot modify system profiles")

    update_data = profile_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)
    return profile


@router.delete("/{profile_id}")
async def delete_profile(
    profile_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a profile."""
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if profile.is_system == "true":
        raise HTTPException(status_code=400, detail="Cannot delete system profiles")

    db.delete(profile)
    db.commit()
    return {"message": "Profile deleted"}


@router.get("/{profile_id}/preview", response_model=ProfilePreview)
async def preview_profile(
    profile_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Preview the file structure that would be created."""
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    files = []
    token_summary = {}

    file_structure = profile.file_structure or {}
    token_config = profile.token_config or {}

    # Parse folders
    folders = file_structure.get("folders", [])
    for folder in folders:
        files.append(FilePreview(path=f"{folder}/", type="folder"))

    # Parse files
    for file_def in file_structure.get("files", []):
        folder = file_def.get("folder", "")
        name = file_def.get("name", "")
        token_type = file_def.get("type", "")
        path = f"{folder}/{name}" if folder else name
        files.append(FilePreview(path=path, type="file", token_type=token_type))

        # Count tokens
        if token_type:
            token_summary[token_type] = token_summary.get(token_type, 0) + 1

    return ProfilePreview(
        profile_id=profile_id,
        files=files,
        token_summary=token_summary,
    )
