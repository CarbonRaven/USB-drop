"""Campaigns router."""

from datetime import datetime, date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uuid

from app.database import get_db
from app.models.campaign import Campaign, CampaignStatus
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter()


# Pydantic models
class CampaignCreate(BaseModel):
    name: str
    client_name: Optional[str] = None
    description: Optional[str] = None
    target_drive_count: int = 0
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    client_name: Optional[str] = None
    description: Optional[str] = None
    target_drive_count: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[CampaignStatus] = None
    notes: Optional[str] = None


class CampaignResponse(BaseModel):
    id: uuid.UUID
    name: str
    client_name: Optional[str]
    description: Optional[str]
    target_drive_count: int
    start_date: Optional[date]
    end_date: Optional[date]
    status: CampaignStatus
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    drive_count: int
    deployed_count: int
    triggered_count: int

    class Config:
        from_attributes = True


class CampaignStats(BaseModel):
    total_drives: int
    created: int
    prepared: int
    deployed: int
    triggered: int
    recovered: int
    total_triggers: int
    unique_ips: int


@router.get("", response_model=List[CampaignResponse])
async def list_campaigns(
    status: Optional[CampaignStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all campaigns."""
    query = db.query(Campaign)
    if status:
        query = query.filter(Campaign.status == status)
    query = query.order_by(Campaign.created_at.desc())
    campaigns = query.offset(skip).limit(limit).all()
    return campaigns


@router.post("", response_model=CampaignResponse)
async def create_campaign(
    campaign_data: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new campaign."""
    campaign = Campaign(**campaign_data.model_dump())
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get campaign by ID."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: uuid.UUID,
    campaign_data: CampaignUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a campaign."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    update_data = campaign_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(campaign, key, value)

    db.commit()
    db.refresh(campaign)
    return campaign


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a campaign."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    db.delete(campaign)
    db.commit()
    return {"message": "Campaign deleted"}


@router.get("/{campaign_id}/stats", response_model=CampaignStats)
async def get_campaign_stats(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get campaign statistics."""
    from app.models.drive import Drive, DriveStatus
    from app.models.trigger import Trigger

    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    drives = campaign.drives or []

    # Count by status
    status_counts = {
        "created": 0,
        "prepared": 0,
        "deployed": 0,
        "triggered": 0,
        "recovered": 0,
    }
    for drive in drives:
        status_counts[drive.status.value] += 1

    # Get all triggers for this campaign
    drive_ids = [d.id for d in drives]
    triggers = []
    if drive_ids:
        from app.models.token import Token
        triggers = db.query(Trigger).join(Token).filter(Token.drive_id.in_(drive_ids)).all()

    unique_ips = set()
    for trigger in triggers:
        if trigger.source_ip:
            unique_ips.add(str(trigger.source_ip))

    return CampaignStats(
        total_drives=len(drives),
        created=status_counts["created"],
        prepared=status_counts["prepared"],
        deployed=status_counts["deployed"],
        triggered=status_counts["triggered"],
        recovered=status_counts["recovered"],
        total_triggers=len(triggers),
        unique_ips=len(unique_ips),
    )
