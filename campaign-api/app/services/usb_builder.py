"""USB Drive builder service - creates tokens and prepares ZIP files."""

import os
import io
import zipfile
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
import logging

from app.models.drive import Drive
from app.models.profile import Profile
from app.models.token import Token
from app.services.canary_client import CanaryTokensClient
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Mapping of token types to file extensions
TOKEN_EXTENSIONS = {
    "doc-msword": ".docx",
    "doc-msexcel": ".xlsx",
    "pdf-acrobat-reader": ".pdf",
    "windows-dir": ".ini",
    "qr-code": ".png",
    "aws-id": ".txt",
    "kubeconfig": ".yaml",
    "wireguard": ".conf",
}


class USBBuilder:
    """Service for building USB drive content."""

    def __init__(self, db: Session):
        self.db = db
        self.canary_client = CanaryTokensClient()
        self.uploads_dir = "uploads"

    async def prepare_drive(self, drive: Drive, profile: Profile) -> dict:
        """
        Prepare a drive by creating all tokens defined in the profile.

        Returns:
            Files manifest dictionary
        """
        token_config = profile.token_config or {}
        file_structure = profile.file_structure or {}

        files = []
        total_size = 0

        # Create folders
        folders = file_structure.get("folders", [])

        # Process file definitions
        for file_def in file_structure.get("files", []):
            filename = file_def.get("name", "")
            folder = file_def.get("folder", "")
            token_type = file_def.get("type", "")
            redirect_theme = file_def.get("redirect_theme", "")

            if not filename or not token_type:
                continue

            # Build file path
            file_path = f"{folder}/{filename}" if folder else filename

            # Create memo for this token
            memo = f"{drive.unique_code}|{file_path}"

            # Determine redirect URL
            redirect_url = None
            if redirect_theme:
                redirect_url = self._get_redirect_url(redirect_theme)

            # Create the token
            try:
                result = await self._create_token(
                    token_type=token_type,
                    memo=memo,
                    redirect_url=redirect_url,
                )

                if not result:
                    logger.error(f"Failed to create token for {file_path}")
                    continue

                # Extract token data
                canary_data = result.get("canarytoken", {})
                canary_token_id = canary_data.get("canarytoken", "")
                token_url = canary_data.get("url", "") or canary_data.get("hostname", "")

                # Create token record
                token = Token(
                    drive_id=drive.id,
                    canary_token_id=canary_token_id,
                    token_type=token_type,
                    filename=filename,
                    file_path=file_path,
                    memo=memo,
                    url=token_url,
                    redirect_url=redirect_url,
                    redirect_theme=redirect_theme,
                    aws_access_key_id=canary_data.get("access_key_id"),
                    aws_secret_access_key=canary_data.get("secret_access_key"),
                )
                self.db.add(token)

                # Download file content for document tokens
                file_content = None
                if token_type in ["doc-msword", "doc-msexcel", "pdf-acrobat-reader", "qr-code"]:
                    try:
                        file_content = await self.canary_client.download_token(canary_token_id)
                    except Exception as e:
                        logger.error(f"Failed to download token file: {e}")

                file_size = len(file_content) if file_content else 0
                total_size += file_size

                files.append({
                    "path": file_path,
                    "token_id": canary_token_id,
                    "token_type": token_type,
                    "size_bytes": file_size,
                    "created_at": datetime.utcnow().isoformat(),
                    "has_content": file_content is not None,
                })

            except Exception as e:
                logger.error(f"Error creating token for {file_path}: {e}")
                continue

        self.db.commit()

        return {
            "folders": folders,
            "files": files,
            "total_size_bytes": total_size,
            "file_count": len(files),
            "prepared_at": datetime.utcnow().isoformat(),
        }

    async def _create_token(
        self,
        token_type: str,
        memo: str,
        redirect_url: Optional[str] = None,
    ) -> Optional[dict]:
        """Create a token using the appropriate method."""
        try:
            if token_type == "dns":
                return await self.canary_client.create_dns_token(memo)
            elif token_type == "doc-msword":
                return await self.canary_client.create_word_token(memo)
            elif token_type == "doc-msexcel":
                return await self.canary_client.create_excel_token(memo)
            elif token_type == "pdf-acrobat-reader":
                return await self.canary_client.create_pdf_token(memo)
            elif token_type == "windows-dir":
                return await self.canary_client.create_folder_token(memo)
            elif token_type == "aws-id":
                return await self.canary_client.create_aws_token(memo)
            elif token_type == "qr-code":
                return await self.canary_client.create_qr_token(memo, redirect_url or "https://example.com")
            elif token_type == "http":
                return await self.canary_client.create_web_token(memo, redirect_url)
            else:
                logger.warning(f"Unknown token type: {token_type}")
                return await self.canary_client.create_token(kind=token_type, memo=memo)
        except Exception as e:
            logger.error(f"Failed to create {token_type} token: {e}")
            return None

    def _get_redirect_url(self, theme: str) -> str:
        """Get redirect URL based on theme."""
        app_domain = settings.canary_domain.replace("subproject55.com", "becomeaninternetghost.com")
        base_url = f"https://rick.{app_domain}"

        theme_urls = {
            "rickroll": f"{base_url}/direct",
            "corporate": f"{base_url}/corporate",
            "login": f"{base_url}/login",
            "maintenance": f"{base_url}/maintenance",
        }

        return theme_urls.get(theme, f"{base_url}/direct")

    async def create_zip(self, drive: Drive) -> bytes:
        """Create a ZIP file containing all drive files."""
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            manifest = drive.files_manifest or {}
            files = manifest.get("files", [])

            # Create folders
            for folder in manifest.get("folders", []):
                zf.writestr(f"{folder}/", "")

            # Add files
            for file_info in files:
                file_path = file_info.get("path", "")
                token_id = file_info.get("token_id", "")
                token_type = file_info.get("token_type", "")

                if not file_path or not token_id:
                    continue

                try:
                    # Get file content
                    if token_type in ["doc-msword", "doc-msexcel", "pdf-acrobat-reader", "qr-code"]:
                        content = await self.canary_client.download_token(token_id)
                        zf.writestr(file_path, content)

                    elif token_type == "windows-dir":
                        # Create desktop.ini for folder token
                        token = self.db.query(Token).filter(
                            Token.canary_token_id == token_id
                        ).first()
                        if token and token.url:
                            ini_content = self._create_desktop_ini(token.url)
                            zf.writestr(file_path, ini_content)

                    elif token_type == "aws-id":
                        # Create AWS credentials file
                        token = self.db.query(Token).filter(
                            Token.canary_token_id == token_id
                        ).first()
                        if token:
                            creds_content = self._create_aws_credentials(
                                token.aws_access_key_id,
                                token.aws_secret_access_key,
                            )
                            zf.writestr(file_path, creds_content)

                except Exception as e:
                    logger.error(f"Error adding file {file_path} to ZIP: {e}")
                    continue

            # Add README
            readme_content = self._create_readme(drive)
            zf.writestr("_README.txt", readme_content)

        zip_buffer.seek(0)
        return zip_buffer.read()

    def _create_desktop_ini(self, hostname: str) -> str:
        """Create desktop.ini content for folder token."""
        return f"""[.ShellClassInfo]
IconResource=\\\\{hostname}\\icon.ico,0
"""

    def _create_aws_credentials(
        self,
        access_key_id: Optional[str],
        secret_access_key: Optional[str],
    ) -> str:
        """Create AWS credentials file content."""
        return f"""[default]
aws_access_key_id = {access_key_id or 'AKIAXXXXXXXXXXXXXXXX'}
aws_secret_access_key = {secret_access_key or 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'}
"""

    def _create_readme(self, drive: Drive) -> str:
        """Create README content for the drive."""
        return f"""USB Drive: {drive.unique_code}
Created: {drive.created_at.strftime('%Y-%m-%d %H:%M:%S')}
Profile: {drive.profile.name if drive.profile else 'Custom'}

This drive contains files for security testing purposes.
"""
