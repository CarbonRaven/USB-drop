"""Webhooks router - receive alerts from CanaryTokens."""

from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import logging

from app.database import SessionLocal
from app.models.token import Token
from app.models.trigger import Trigger
from app.models.drive import Drive, DriveStatus
from app.services.slack_notifier import SlackNotifier
from app.services.geo_service import GeoService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/canary")
async def receive_canary_alert(
    request: Request,
    background_tasks: BackgroundTasks
):
    """Receive webhook alerts from CanaryTokens server."""
    try:
        # Parse request body
        content_type = request.headers.get("content-type", "")

        if "application/json" in content_type:
            payload = await request.json()
        else:
            # Form data
            form = await request.form()
            payload = dict(form)

        logger.info(f"Received canary alert: {payload}")

        # Extract token ID from payload
        # CanaryTokens sends various formats depending on token type
        canary_token_id = payload.get("token") or payload.get("canarytoken") or payload.get("memo", "").split("|")[0] if "|" in payload.get("memo", "") else None

        if not canary_token_id:
            # Try to extract from memo field
            memo = payload.get("memo", "")
            if memo:
                canary_token_id = memo

        if not canary_token_id:
            logger.warning(f"Could not extract token ID from payload: {payload}")
            return {"status": "received", "warning": "Could not identify token"}

        # Process alert in background
        background_tasks.add_task(
            process_alert,
            canary_token_id=canary_token_id,
            payload=payload
        )

        return {"status": "received"}

    except Exception as e:
        logger.error(f"Error processing canary alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_alert(canary_token_id: str, payload: dict):
    """Process an incoming alert."""
    db = SessionLocal()
    try:
        # Find token in database
        token = db.query(Token).filter(Token.canary_token_id == canary_token_id).first()

        if not token:
            # Try partial match on memo
            memo = payload.get("memo", "")
            if memo:
                token = db.query(Token).filter(Token.memo.contains(memo)).first()

        if not token:
            logger.warning(f"Token not found: {canary_token_id}")
            return

        # Extract source IP
        source_ip = (
            payload.get("src_ip") or
            payload.get("ip") or
            payload.get("source_ip")
        )

        # Get geo data
        geo_data = {}
        if source_ip:
            try:
                geo_service = GeoService()
                geo_data = await geo_service.lookup(source_ip)
            except Exception as e:
                logger.error(f"Geo lookup failed: {e}")

        # Create trigger record
        trigger = Trigger(
            token_id=token.id,
            source_ip=source_ip,
            user_agent=payload.get("useragent") or payload.get("user_agent"),
            geo_city=geo_data.get("city"),
            geo_region=geo_data.get("region"),
            geo_country=geo_data.get("country"),
            geo_country_code=geo_data.get("country_code"),
            geo_latitude=geo_data.get("latitude"),
            geo_longitude=geo_data.get("longitude"),
            geo_isp=geo_data.get("isp"),
            geo_org=geo_data.get("org"),
            additional_data=payload,
            raw_payload=payload,
            triggered_at=datetime.utcnow(),
        )
        db.add(trigger)

        # Update token timestamps
        now = datetime.utcnow()
        if not token.first_triggered_at:
            token.first_triggered_at = now
        token.last_triggered_at = now

        # Update drive status
        drive = db.query(Drive).filter(Drive.id == token.drive_id).first()
        if drive and drive.status in [DriveStatus.DEPLOYED, DriveStatus.PREPARED]:
            drive.status = DriveStatus.TRIGGERED
            if not drive.triggered_at:
                drive.triggered_at = now

        db.commit()

        # Send Slack notification
        try:
            notifier = SlackNotifier()
            await notifier.send_trigger_alert(
                token=token,
                trigger=trigger,
                drive=drive,
            )
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")

        logger.info(f"Processed trigger for token {canary_token_id}")

    except Exception as e:
        logger.error(f"Error processing alert: {e}")
        db.rollback()
    finally:
        db.close()
