"""Slack notification service."""

import httpx
from typing import Optional
import logging

from app.config import get_settings
from app.models.token import Token
from app.models.trigger import Trigger
from app.models.drive import Drive

logger = logging.getLogger(__name__)
settings = get_settings()


class SlackNotifier:
    """Service for sending Slack notifications."""

    def __init__(self):
        self.webhook_url = settings.slack_webhook_url
        self.enabled = bool(self.webhook_url)

    async def send_message(self, blocks: list, text: str = "USB Drop Alert"):
        """Send a message to Slack."""
        if not self.enabled:
            logger.debug("Slack notifications disabled - no webhook URL configured")
            return

        payload = {
            "text": text,
            "blocks": blocks,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.webhook_url, json=payload)
                response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")

    async def send_trigger_alert(
        self,
        token: Token,
        trigger: Trigger,
        drive: Optional[Drive] = None,
    ):
        """Send an alert when a token is triggered."""
        if not self.enabled:
            return

        # Build location string
        location_parts = []
        if trigger.geo_city:
            location_parts.append(trigger.geo_city)
        if trigger.geo_country:
            location_parts.append(trigger.geo_country)
        location = ", ".join(location_parts) if location_parts else "Unknown"

        # Build blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚨 USB Drop Token Triggered!",
                    "emoji": True,
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Drive:*\n{drive.unique_code if drive else 'Unknown'}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Token Type:*\n{token.token_type}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*File:*\n{token.filename or 'N/A'}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Source IP:*\n{trigger.source_ip or 'Unknown'}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Location:*\n{location}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:*\n{trigger.triggered_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    },
                ]
            },
        ]

        # Add user agent if available
        if trigger.user_agent:
            # Truncate long user agents
            ua = trigger.user_agent[:100] + "..." if len(trigger.user_agent) > 100 else trigger.user_agent
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"*User Agent:* {ua}"
                    }
                ]
            })

        # Add drive label if available
        if drive and drive.label:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Drive Label:* {drive.label}"
                    }
                ]
            })

        await self.send_message(
            blocks=blocks,
            text=f"🚨 Token triggered: {drive.unique_code if drive else 'Unknown'} - {token.token_type}",
        )

    async def send_deployment_alert(self, drive: Drive, location_name: str = None):
        """Send an alert when a drive is deployed."""
        if not self.enabled:
            return

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📍 USB Drive Deployed",
                    "emoji": True,
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Drive:*\n{drive.unique_code}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Location:*\n{location_name or 'Not specified'}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Label:*\n{drive.label or 'None'}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Campaign:*\n{drive.campaign.name if drive.campaign else 'Unknown'}"
                    },
                ]
            },
        ]

        await self.send_message(
            blocks=blocks,
            text=f"📍 Drive deployed: {drive.unique_code} at {location_name or 'unknown location'}",
        )
