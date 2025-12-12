"""Reports router."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uuid
import io
import csv

from app.database import get_db
from app.models.campaign import Campaign
from app.models.drive import Drive
from app.models.token import Token
from app.models.trigger import Trigger
from app.models.deployment import Deployment
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter()


class CampaignReport(BaseModel):
    campaign_id: uuid.UUID
    campaign_name: str
    client_name: Optional[str]
    status: str
    start_date: Optional[str]
    end_date: Optional[str]
    total_drives: int
    drives_deployed: int
    drives_triggered: int
    total_tokens: int
    total_triggers: int
    unique_source_ips: int
    first_trigger: Optional[datetime]
    last_trigger: Optional[datetime]
    drives: list


@router.get("/campaign/{campaign_id}", response_model=CampaignReport)
async def get_campaign_report(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed campaign report."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    drives = campaign.drives or []

    # Collect stats
    total_tokens = 0
    total_triggers = 0
    unique_ips = set()
    first_trigger = None
    last_trigger = None
    drives_deployed = 0
    drives_triggered = 0

    drive_details = []

    for drive in drives:
        if drive.status.value in ["deployed", "triggered", "recovered"]:
            drives_deployed += 1
        if drive.status.value == "triggered":
            drives_triggered += 1

        tokens = drive.tokens or []
        total_tokens += len(tokens)

        drive_triggers = 0
        for token in tokens:
            triggers = token.triggers or []
            drive_triggers += len(triggers)
            total_triggers += len(triggers)

            for trigger in triggers:
                if trigger.source_ip:
                    unique_ips.add(str(trigger.source_ip))
                if first_trigger is None or trigger.triggered_at < first_trigger:
                    first_trigger = trigger.triggered_at
                if last_trigger is None or trigger.triggered_at > last_trigger:
                    last_trigger = trigger.triggered_at

        # Get deployment info
        deployment = drive.deployment
        deployment_info = None
        if deployment:
            deployment_info = {
                "location_name": deployment.location_name,
                "latitude": float(deployment.latitude) if deployment.latitude else None,
                "longitude": float(deployment.longitude) if deployment.longitude else None,
                "deployed_at": deployment.deployed_at.isoformat() if deployment.deployed_at else None,
            }

        drive_details.append({
            "unique_code": drive.unique_code,
            "status": drive.status.value,
            "label": drive.label,
            "token_count": len(tokens),
            "trigger_count": drive_triggers,
            "deployment": deployment_info,
            "created_at": drive.created_at.isoformat(),
        })

    return CampaignReport(
        campaign_id=campaign.id,
        campaign_name=campaign.name,
        client_name=campaign.client_name,
        status=campaign.status.value,
        start_date=campaign.start_date.isoformat() if campaign.start_date else None,
        end_date=campaign.end_date.isoformat() if campaign.end_date else None,
        total_drives=len(drives),
        drives_deployed=drives_deployed,
        drives_triggered=drives_triggered,
        total_tokens=total_tokens,
        total_triggers=total_triggers,
        unique_source_ips=len(unique_ips),
        first_trigger=first_trigger,
        last_trigger=last_trigger,
        drives=drive_details,
    )


@router.get("/export/{campaign_id}/csv")
async def export_campaign_csv(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export campaign data as CSV."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        "Drive Code", "Drive Status", "Drive Label",
        "Token Type", "Token Filename",
        "Trigger Time", "Source IP", "City", "Country", "User Agent",
        "Deployment Location", "Deployment Time"
    ])

    # Write data
    for drive in campaign.drives or []:
        deployment = drive.deployment
        dep_location = deployment.location_name if deployment else ""
        dep_time = deployment.deployed_at.isoformat() if deployment and deployment.deployed_at else ""

        for token in drive.tokens or []:
            if token.triggers:
                for trigger in token.triggers:
                    writer.writerow([
                        drive.unique_code,
                        drive.status.value,
                        drive.label or "",
                        token.token_type,
                        token.filename or "",
                        trigger.triggered_at.isoformat() if trigger.triggered_at else "",
                        str(trigger.source_ip) if trigger.source_ip else "",
                        trigger.geo_city or "",
                        trigger.geo_country or "",
                        trigger.user_agent or "",
                        dep_location,
                        dep_time,
                    ])
            else:
                # Token with no triggers
                writer.writerow([
                    drive.unique_code,
                    drive.status.value,
                    drive.label or "",
                    token.token_type,
                    token.filename or "",
                    "", "", "", "", "",
                    dep_location,
                    dep_time,
                ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={campaign.name.replace(' ', '_')}_report.csv"
        }
    )


@router.get("/summary")
async def get_summary_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overall system summary statistics."""
    from app.models.campaign import CampaignStatus

    campaigns = db.query(Campaign).all()
    drives = db.query(Drive).all()
    triggers = db.query(Trigger).all()

    active_campaigns = sum(1 for c in campaigns if c.status == CampaignStatus.ACTIVE)

    return {
        "total_campaigns": len(campaigns),
        "active_campaigns": active_campaigns,
        "total_drives": len(drives),
        "total_triggers": len(triggers),
        "drives_by_status": {
            "created": sum(1 for d in drives if d.status.value == "created"),
            "prepared": sum(1 for d in drives if d.status.value == "prepared"),
            "deployed": sum(1 for d in drives if d.status.value == "deployed"),
            "triggered": sum(1 for d in drives if d.status.value == "triggered"),
            "recovered": sum(1 for d in drives if d.status.value == "recovered"),
        }
    }
