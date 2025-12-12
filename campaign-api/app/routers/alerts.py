"""Alerts router - view and search trigger events."""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
import uuid

from app.database import get_db
from app.models.trigger import Trigger
from app.models.token import Token
from app.models.drive import Drive
from app.models.campaign import Campaign
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter()


class TriggerDetail(BaseModel):
    id: uuid.UUID
    token_id: uuid.UUID
    token_type: str
    token_filename: Optional[str]
    drive_code: str
    campaign_name: str
    source_ip: Optional[str]
    user_agent: Optional[str]
    geo_city: Optional[str]
    geo_country: Optional[str]
    geo_latitude: Optional[float]
    geo_longitude: Optional[float]
    triggered_at: datetime

    class Config:
        from_attributes = True


class MapPoint(BaseModel):
    id: uuid.UUID
    type: str  # "deployment" or "trigger"
    latitude: float
    longitude: float
    label: str
    drive_code: str
    timestamp: datetime
    details: dict


class AlertStats(BaseModel):
    total_triggers: int
    triggers_today: int
    triggers_week: int
    unique_ips: int
    unique_drives: int


@router.get("", response_model=List[TriggerDetail])
async def list_alerts(
    campaign_id: Optional[uuid.UUID] = None,
    drive_id: Optional[uuid.UUID] = None,
    days: int = Query(30, ge=1, le=365),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all trigger alerts."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    query = db.query(Trigger).join(Token).join(Drive).join(Campaign)
    query = query.filter(Trigger.triggered_at >= cutoff)

    if campaign_id:
        query = query.filter(Campaign.id == campaign_id)
    if drive_id:
        query = query.filter(Drive.id == drive_id)

    query = query.order_by(Trigger.triggered_at.desc())
    triggers = query.offset(skip).limit(limit).all()

    results = []
    for trigger in triggers:
        token = trigger.token
        drive = token.drive
        campaign = drive.campaign

        results.append(TriggerDetail(
            id=trigger.id,
            token_id=token.id,
            token_type=token.token_type,
            token_filename=token.filename,
            drive_code=drive.unique_code,
            campaign_name=campaign.name,
            source_ip=str(trigger.source_ip) if trigger.source_ip else None,
            user_agent=trigger.user_agent,
            geo_city=trigger.geo_city,
            geo_country=trigger.geo_country,
            geo_latitude=float(trigger.geo_latitude) if trigger.geo_latitude else None,
            geo_longitude=float(trigger.geo_longitude) if trigger.geo_longitude else None,
            triggered_at=trigger.triggered_at,
        ))

    return results


@router.get("/recent", response_model=List[TriggerDetail])
async def recent_alerts(
    hours: int = Query(24, ge=1, le=168),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recent alerts (last N hours)."""
    cutoff = datetime.utcnow() - timedelta(hours=hours)

    triggers = db.query(Trigger).filter(
        Trigger.triggered_at >= cutoff
    ).order_by(Trigger.triggered_at.desc()).limit(100).all()

    results = []
    for trigger in triggers:
        token = trigger.token
        drive = token.drive
        campaign = drive.campaign

        results.append(TriggerDetail(
            id=trigger.id,
            token_id=token.id,
            token_type=token.token_type,
            token_filename=token.filename,
            drive_code=drive.unique_code,
            campaign_name=campaign.name,
            source_ip=str(trigger.source_ip) if trigger.source_ip else None,
            user_agent=trigger.user_agent,
            geo_city=trigger.geo_city,
            geo_country=trigger.geo_country,
            geo_latitude=float(trigger.geo_latitude) if trigger.geo_latitude else None,
            geo_longitude=float(trigger.geo_longitude) if trigger.geo_longitude else None,
            triggered_at=trigger.triggered_at,
        ))

    return results


@router.get("/stats", response_model=AlertStats)
async def alert_stats(
    campaign_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get alert statistics."""
    from app.models.deployment import Deployment

    query = db.query(Trigger).join(Token).join(Drive)
    if campaign_id:
        query = query.filter(Drive.campaign_id == campaign_id)

    all_triggers = query.all()

    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)

    unique_ips = set()
    unique_drives = set()
    today_count = 0
    week_count = 0

    for trigger in all_triggers:
        if trigger.source_ip:
            unique_ips.add(str(trigger.source_ip))
        unique_drives.add(trigger.token.drive_id)

        if trigger.triggered_at >= today_start:
            today_count += 1
        if trigger.triggered_at >= week_start:
            week_count += 1

    return AlertStats(
        total_triggers=len(all_triggers),
        triggers_today=today_count,
        triggers_week=week_count,
        unique_ips=len(unique_ips),
        unique_drives=len(unique_drives),
    )


@router.get("/map", response_model=List[MapPoint])
async def map_data(
    campaign_id: Optional[uuid.UUID] = None,
    include_deployments: bool = True,
    include_triggers: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get data for map visualization."""
    from app.models.deployment import Deployment

    points = []

    # Get deployments
    if include_deployments:
        dep_query = db.query(Deployment).join(Drive)
        if campaign_id:
            dep_query = dep_query.filter(Drive.campaign_id == campaign_id)
        deployments = dep_query.all()

        for dep in deployments:
            if dep.latitude and dep.longitude:
                drive = dep.drive
                points.append(MapPoint(
                    id=dep.id,
                    type="deployment",
                    latitude=float(dep.latitude),
                    longitude=float(dep.longitude),
                    label=f"Dropped: {drive.unique_code}",
                    drive_code=drive.unique_code,
                    timestamp=dep.deployed_at,
                    details={
                        "location_name": dep.location_name,
                        "location_type": dep.location_type,
                        "deployed_by": dep.deployed_by,
                    }
                ))

    # Get triggers with geo data
    if include_triggers:
        trig_query = db.query(Trigger).join(Token).join(Drive)
        if campaign_id:
            trig_query = trig_query.filter(Drive.campaign_id == campaign_id)
        trig_query = trig_query.filter(
            Trigger.geo_latitude.isnot(None),
            Trigger.geo_longitude.isnot(None)
        )
        triggers = trig_query.all()

        for trigger in triggers:
            token = trigger.token
            drive = token.drive
            points.append(MapPoint(
                id=trigger.id,
                type="trigger",
                latitude=float(trigger.geo_latitude),
                longitude=float(trigger.geo_longitude),
                label=f"Triggered: {drive.unique_code}",
                drive_code=drive.unique_code,
                timestamp=trigger.triggered_at,
                details={
                    "token_type": token.token_type,
                    "source_ip": str(trigger.source_ip) if trigger.source_ip else None,
                    "city": trigger.geo_city,
                    "country": trigger.geo_country,
                }
            ))

    return points
