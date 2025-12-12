"""Drives router - USB drive management."""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uuid
import io
import zipfile

from app.database import get_db
from app.models.drive import Drive, DriveStatus
from app.models.campaign import Campaign
from app.models.profile import Profile
from app.models.deployment import Deployment
from app.models.token import Token
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.canary_client import CanaryTokensClient
from app.services.usb_builder import USBBuilder

router = APIRouter()


# Pydantic models
class DriveCreate(BaseModel):
    campaign_id: uuid.UUID
    profile_id: Optional[uuid.UUID] = None
    label: Optional[str] = None
    drive_brand: Optional[str] = None
    drive_capacity: Optional[str] = None
    notes: Optional[str] = None


class DriveUpdate(BaseModel):
    label: Optional[str] = None
    drive_brand: Optional[str] = None
    drive_capacity: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[DriveStatus] = None


class DeploymentCreate(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None
    location_description: Optional[str] = None
    location_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    deployed_by: Optional[str] = None
    deployment_notes: Optional[str] = None


class DriveResponse(BaseModel):
    id: uuid.UUID
    campaign_id: uuid.UUID
    profile_id: Optional[uuid.UUID]
    unique_code: str
    status: DriveStatus
    label: Optional[str]
    drive_brand: Optional[str]
    drive_capacity: Optional[str]
    files_manifest: dict
    notes: Optional[str]
    created_at: datetime
    prepared_at: Optional[datetime]
    deployed_at: Optional[datetime]
    triggered_at: Optional[datetime]
    trigger_count: int

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    id: uuid.UUID
    canary_token_id: str
    token_type: str
    filename: Optional[str]
    memo: Optional[str]
    url: Optional[str]
    created_at: datetime
    is_triggered: bool
    trigger_count: int

    class Config:
        from_attributes = True


class DeploymentResponse(BaseModel):
    id: uuid.UUID
    drive_id: uuid.UUID
    latitude: Optional[float]
    longitude: Optional[float]
    location_name: Optional[str]
    location_description: Optional[str]
    deployed_by: Optional[str]
    deployed_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[DriveResponse])
async def list_drives(
    campaign_id: Optional[uuid.UUID] = None,
    status: Optional[DriveStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all drives."""
    query = db.query(Drive)
    if campaign_id:
        query = query.filter(Drive.campaign_id == campaign_id)
    if status:
        query = query.filter(Drive.status == status)
    query = query.order_by(Drive.created_at.desc())
    drives = query.offset(skip).limit(limit).all()
    return drives


@router.post("", response_model=DriveResponse)
async def create_drive(
    drive_data: DriveCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new drive record."""
    # Verify campaign exists
    campaign = db.query(Campaign).filter(Campaign.id == drive_data.campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Verify profile exists if provided
    if drive_data.profile_id:
        profile = db.query(Profile).filter(Profile.id == drive_data.profile_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

    drive = Drive(**drive_data.model_dump())
    db.add(drive)
    db.commit()
    db.refresh(drive)
    return drive


@router.get("/by-code/{code}", response_model=DriveResponse)
async def get_drive_by_code(
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get drive by unique code."""
    drive = db.query(Drive).filter(Drive.unique_code == code).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")
    return drive


@router.get("/{drive_id}", response_model=DriveResponse)
async def get_drive(
    drive_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get drive by ID."""
    drive = db.query(Drive).filter(Drive.id == drive_id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")
    return drive


@router.put("/{drive_id}", response_model=DriveResponse)
async def update_drive(
    drive_id: uuid.UUID,
    drive_data: DriveUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a drive."""
    drive = db.query(Drive).filter(Drive.id == drive_id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")

    update_data = drive_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(drive, key, value)

    db.commit()
    db.refresh(drive)
    return drive


@router.post("/{drive_id}/prepare", response_model=DriveResponse)
async def prepare_drive(
    drive_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Prepare a drive - create tokens based on profile."""
    drive = db.query(Drive).filter(Drive.id == drive_id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")

    if not drive.profile_id:
        raise HTTPException(status_code=400, detail="Drive has no profile assigned")

    if drive.status != DriveStatus.CREATED:
        raise HTTPException(status_code=400, detail="Drive is already prepared")

    profile = db.query(Profile).filter(Profile.id == drive.profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Create tokens using CanaryTokens API
    try:
        builder = USBBuilder(db)
        files_manifest = await builder.prepare_drive(drive, profile)

        drive.files_manifest = files_manifest
        drive.status = DriveStatus.PREPARED
        drive.prepared_at = datetime.utcnow()
        db.commit()
        db.refresh(drive)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to prepare drive: {str(e)}")

    return drive


@router.get("/{drive_id}/download")
async def download_drive_zip(
    drive_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download a ZIP file containing all drive files."""
    drive = db.query(Drive).filter(Drive.id == drive_id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")

    if drive.status == DriveStatus.CREATED:
        raise HTTPException(status_code=400, detail="Drive not prepared yet")

    # Build ZIP file in memory
    try:
        builder = USBBuilder(db)
        zip_buffer = await builder.create_zip(drive)

        return StreamingResponse(
            io.BytesIO(zip_buffer),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={drive.unique_code}.zip"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create ZIP: {str(e)}")


@router.post("/{drive_id}/deploy", response_model=DeploymentResponse)
async def deploy_drive(
    drive_id: uuid.UUID,
    deployment_data: DeploymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record deployment of a drive."""
    drive = db.query(Drive).filter(Drive.id == drive_id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")

    if drive.status not in [DriveStatus.PREPARED, DriveStatus.DEPLOYED]:
        raise HTTPException(status_code=400, detail="Drive must be prepared before deployment")

    # Check if already deployed
    existing = db.query(Deployment).filter(Deployment.drive_id == drive_id).first()
    if existing:
        # Update existing deployment
        for key, value in deployment_data.model_dump(exclude_unset=True).items():
            setattr(existing, key, value)
        existing.deployed_at = datetime.utcnow()
        deployment = existing
    else:
        # Create new deployment
        deployment = Deployment(
            drive_id=drive_id,
            **deployment_data.model_dump()
        )
        db.add(deployment)

    # Update drive status
    drive.status = DriveStatus.DEPLOYED
    drive.deployed_at = datetime.utcnow()

    db.commit()
    db.refresh(deployment)
    return deployment


@router.get("/{drive_id}/tokens", response_model=List[TokenResponse])
async def get_drive_tokens(
    drive_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all tokens for a drive."""
    drive = db.query(Drive).filter(Drive.id == drive_id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")

    return drive.tokens or []


@router.get("/{drive_id}/deployment", response_model=DeploymentResponse)
async def get_drive_deployment(
    drive_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get deployment info for a drive."""
    deployment = db.query(Deployment).filter(Deployment.drive_id == drive_id).first()
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")

    return deployment
