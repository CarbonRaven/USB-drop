"""Geolocation service for IP lookups."""

import httpx
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class GeoService:
    """Service for IP geolocation lookups."""

    def __init__(self):
        # Using ip-api.com (free tier: 45 requests/minute)
        self.api_url = "http://ip-api.com/json"
        self.timeout = 5.0

    async def lookup(self, ip_address: str) -> dict:
        """
        Look up geolocation data for an IP address.

        Returns:
            Dictionary with location data or empty dict on failure
        """
        if not ip_address or ip_address in ["127.0.0.1", "::1", "localhost"]:
            return {}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.api_url}/{ip_address}",
                    params={"fields": "status,country,countryCode,region,regionName,city,lat,lon,isp,org"},
                )
                response.raise_for_status()
                data = response.json()

                if data.get("status") != "success":
                    logger.warning(f"Geo lookup failed for {ip_address}: {data}")
                    return {}

                return {
                    "country": data.get("country"),
                    "country_code": data.get("countryCode"),
                    "region": data.get("regionName"),
                    "city": data.get("city"),
                    "latitude": data.get("lat"),
                    "longitude": data.get("lon"),
                    "isp": data.get("isp"),
                    "org": data.get("org"),
                }

        except Exception as e:
            logger.error(f"Geo lookup error for {ip_address}: {e}")
            return {}

    async def batch_lookup(self, ip_addresses: list[str]) -> dict[str, dict]:
        """
        Look up geolocation for multiple IP addresses.

        Returns:
            Dictionary mapping IP addresses to their geo data
        """
        results = {}
        for ip in ip_addresses:
            results[ip] = await self.lookup(ip)
        return results
