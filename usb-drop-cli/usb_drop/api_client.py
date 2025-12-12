"""API client for USB Drop Campaign Manager."""

from typing import Any, Dict, List, Optional

import requests

from .config import config


class APIError(Exception):
    """API error with status code and message."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error {status_code}: {message}")


class APIClient:
    """Client for interacting with the USB Drop API."""

    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        self.api_url = (api_url or config.api_url or "").rstrip("/")
        self.api_key = api_key or config.api_key
        self.session = requests.Session()
        if self.api_key:
            self.session.headers["X-API-Key"] = self.api_key

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        stream: bool = False,
    ) -> Any:
        """Make an API request."""
        url = f"{self.api_url}{endpoint}"

        try:
            response = self.session.request(
                method,
                url,
                json=data,
                params=params,
                stream=stream,
            )
        except requests.RequestException as e:
            raise APIError(0, f"Connection error: {e}")

        if not response.ok:
            try:
                error_data = response.json()
                message = error_data.get("detail", response.text)
            except ValueError:
                message = response.text
            raise APIError(response.status_code, message)

        if stream:
            return response

        if response.status_code == 204:
            return None

        try:
            return response.json()
        except ValueError:
            return response.text

    # Campaign endpoints
    def list_campaigns(self) -> List[Dict]:
        """List all campaigns."""
        return self._request("GET", "/campaigns")

    def get_campaign(self, campaign_id: str) -> Dict:
        """Get a specific campaign."""
        return self._request("GET", f"/campaigns/{campaign_id}")

    def get_campaign_stats(self, campaign_id: str) -> Dict:
        """Get campaign statistics."""
        return self._request("GET", f"/campaigns/{campaign_id}/stats")

    # Profile endpoints
    def list_profiles(self) -> List[Dict]:
        """List all profiles."""
        return self._request("GET", "/profiles")

    def get_profile(self, profile_id: str) -> Dict:
        """Get a specific profile."""
        return self._request("GET", f"/profiles/{profile_id}")

    def preview_profile(self, profile_id: str) -> Dict:
        """Preview profile file structure."""
        return self._request("GET", f"/profiles/{profile_id}/preview")

    # Drive endpoints
    def list_drives(
        self, campaign_id: Optional[str] = None, status: Optional[str] = None
    ) -> List[Dict]:
        """List drives with optional filters."""
        params = {}
        if campaign_id:
            params["campaign_id"] = campaign_id
        if status:
            params["status"] = status
        return self._request("GET", "/drives", params=params)

    def get_drive(self, drive_id: str) -> Dict:
        """Get a specific drive."""
        return self._request("GET", f"/drives/{drive_id}")

    def get_drive_by_code(self, code: str) -> Dict:
        """Get a drive by its unique code."""
        return self._request("GET", f"/drives/by-code/{code}")

    def create_drive(
        self, campaign_id: str, profile_id: str, label: Optional[str] = None
    ) -> Dict:
        """Create a new drive."""
        data = {
            "campaign_id": campaign_id,
            "profile_id": profile_id,
        }
        if label:
            data["label"] = label
        return self._request("POST", "/drives", data=data)

    def prepare_drive(self, drive_id: str) -> Dict:
        """Prepare a drive (create tokens)."""
        return self._request("POST", f"/drives/{drive_id}/prepare")

    def download_drive(self, drive_id: str) -> requests.Response:
        """Download drive ZIP file."""
        return self._request("GET", f"/drives/{drive_id}/download", stream=True)

    def deploy_drive(
        self,
        drive_id: str,
        latitude: float,
        longitude: float,
        location_description: Optional[str] = None,
        deployed_by: Optional[str] = None,
    ) -> Dict:
        """Record drive deployment."""
        data = {
            "latitude": latitude,
            "longitude": longitude,
        }
        if location_description:
            data["location_description"] = location_description
        if deployed_by:
            data["deployed_by"] = deployed_by
        return self._request("POST", f"/drives/{drive_id}/deploy", data=data)

    def get_drive_tokens(self, drive_id: str) -> List[Dict]:
        """Get tokens for a drive."""
        return self._request("GET", f"/drives/{drive_id}/tokens")

    # Alert endpoints
    def list_alerts(self, hours: int = 24) -> List[Dict]:
        """List recent alerts."""
        return self._request("GET", "/alerts/recent", params={"hours": hours})

    def get_alert_stats(self, campaign_id: Optional[str] = None) -> Dict:
        """Get alert statistics."""
        params = {}
        if campaign_id:
            params["campaign_id"] = campaign_id
        return self._request("GET", "/alerts/stats", params=params)

    # Report endpoints
    def get_campaign_report(self, campaign_id: str) -> Dict:
        """Get campaign report."""
        return self._request("GET", f"/reports/campaign/{campaign_id}")

    def export_campaign_csv(self, campaign_id: str) -> requests.Response:
        """Export campaign data as CSV."""
        return self._request(
            "GET", f"/reports/export/{campaign_id}/csv", stream=True
        )


# Default client instance
client = APIClient()
