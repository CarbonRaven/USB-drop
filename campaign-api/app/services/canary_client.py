"""CanaryTokens API client."""

import httpx
from typing import Optional
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CanaryTokensClient:
    """Client for interacting with self-hosted CanaryTokens API."""

    def __init__(self):
        self.server_url = settings.canary_server.rstrip("/")
        self.factory_auth = settings.factory_auth
        self.timeout = 30.0

    async def create_token(
        self,
        kind: str,
        memo: str,
        email: str = "alerts@example.com",
        redirect_url: Optional[str] = None,
        **kwargs
    ) -> dict:
        """
        Create a new Canarytoken.

        Args:
            kind: Token type (dns, doc-msword, doc-msexcel, etc.)
            memo: Description/identifier for the token
            email: Email address for alerts
            redirect_url: URL for redirect tokens
            **kwargs: Additional token-specific parameters

        Returns:
            API response as dictionary
        """
        url = f"{self.server_url}/api/v1/canarytoken/factory.create"

        payload = {
            "factory_auth": self.factory_auth,
            "kind": kind,
            "memo": memo,
            "email": email,
        }

        if redirect_url:
            payload["redirect_url"] = redirect_url

        payload.update(kwargs)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

    async def download_token(self, token_id: str) -> bytes:
        """
        Download a token file (for document-based tokens).

        Args:
            token_id: The canarytoken ID

        Returns:
            File content as bytes
        """
        url = f"{self.server_url}/api/v1/canarytoken/factory.download"
        params = {
            "factory_auth": self.factory_auth,
            "canarytoken": token_id,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.content

    async def fetch_token(self, token_id: str) -> dict:
        """Fetch details of a Canarytoken."""
        url = f"{self.server_url}/api/v1/canarytoken/factory.fetch"
        params = {
            "factory_auth": self.factory_auth,
            "canarytoken": token_id,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def delete_token(self, token_id: str) -> dict:
        """Delete a Canarytoken."""
        url = f"{self.server_url}/api/v1/canarytoken/factory.delete"

        payload = {
            "factory_auth": self.factory_auth,
            "canarytoken": token_id,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

    async def create_dns_token(self, memo: str) -> dict:
        """Create a DNS token."""
        return await self.create_token(kind="dns", memo=memo)

    async def create_word_token(self, memo: str) -> dict:
        """Create a Word document token."""
        return await self.create_token(kind="doc-msword", memo=memo)

    async def create_excel_token(self, memo: str) -> dict:
        """Create an Excel document token."""
        return await self.create_token(kind="doc-msexcel", memo=memo)

    async def create_pdf_token(self, memo: str) -> dict:
        """Create a PDF token."""
        return await self.create_token(kind="pdf-acrobat-reader", memo=memo)

    async def create_folder_token(self, memo: str) -> dict:
        """Create a Windows folder token."""
        return await self.create_token(kind="windows-dir", memo=memo)

    async def create_aws_token(self, memo: str) -> dict:
        """Create AWS credentials token."""
        return await self.create_token(kind="aws-id", memo=memo)

    async def create_qr_token(self, memo: str, redirect_url: str) -> dict:
        """Create a QR code token."""
        return await self.create_token(
            kind="qr-code",
            memo=memo,
            redirect_url=redirect_url,
        )

    async def create_web_token(self, memo: str, redirect_url: Optional[str] = None) -> dict:
        """Create a web bug token."""
        return await self.create_token(
            kind="http",
            memo=memo,
            redirect_url=redirect_url,
        )
