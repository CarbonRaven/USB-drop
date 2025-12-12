"""Tokens router."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uuid

from app.database import get_db
from app.models.token import Token
from app.models.trigger import Trigger
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.canary_client import CanaryTokensClient

router = APIRouter()


class TokenResponse(BaseModel):
    id: uuid.UUID
    drive_id: uuid.UUID
    canary_token_id: str
    token_type: str
    filename: str | None
    memo: str | None
    url: str | None
    is_triggered: bool
    trigger_count: int

    class Config:
        from_attributes = True


class TriggerResponse(BaseModel):
    id: uuid.UUID
    source_ip: str | None
    user_agent: str | None
    geo_city: str | None
    geo_country: str | None
    triggered_at: str

    class Config:
        from_attributes = True


@router.get("/{token_id}", response_model=TokenResponse)
async def get_token(
    token_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get token details."""
    token = db.query(Token).filter(Token.id == token_id).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    return token


@router.get("/{token_id}/triggers", response_model=List[TriggerResponse])
async def get_token_triggers(
    token_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all triggers for a token."""
    token = db.query(Token).filter(Token.id == token_id).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    triggers = db.query(Trigger).filter(Trigger.token_id == token_id).order_by(
        Trigger.triggered_at.desc()
    ).all()

    return triggers


@router.delete("/{token_id}")
async def delete_token(
    token_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a token."""
    token = db.query(Token).filter(Token.id == token_id).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    # Delete from CanaryTokens server
    try:
        client = CanaryTokensClient()
        await client.delete_token(token.canary_token_id)
    except Exception:
        pass  # Continue even if remote delete fails

    db.delete(token)
    db.commit()
    return {"message": "Token deleted"}
