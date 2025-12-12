"""Configuration management for USB Drop CLI."""

import os
from pathlib import Path
from typing import Optional

import yaml

CONFIG_DIR = Path.home() / ".usb-drop"
CONFIG_FILE = CONFIG_DIR / "config.yaml"


class Config:
    """Manages CLI configuration."""

    def __init__(self):
        self._config = self._load_config()

    def _load_config(self) -> dict:
        """Load configuration from file."""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r") as f:
                return yaml.safe_load(f) or {}
        return {}

    def _save_config(self):
        """Save configuration to file."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            yaml.dump(self._config, f, default_flow_style=False)

    @property
    def api_url(self) -> Optional[str]:
        """Get the API URL."""
        return self._config.get("api_url") or os.environ.get("USB_DROP_API_URL")

    @api_url.setter
    def api_url(self, value: str):
        """Set the API URL."""
        self._config["api_url"] = value
        self._save_config()

    @property
    def api_key(self) -> Optional[str]:
        """Get the API key."""
        return self._config.get("api_key") or os.environ.get("USB_DROP_API_KEY")

    @api_key.setter
    def api_key(self, value: str):
        """Set the API key."""
        self._config["api_key"] = value
        self._save_config()

    @property
    def default_campaign(self) -> Optional[str]:
        """Get the default campaign ID."""
        return self._config.get("default_campaign")

    @default_campaign.setter
    def default_campaign(self, value: str):
        """Set the default campaign ID."""
        self._config["default_campaign"] = value
        self._save_config()

    def is_configured(self) -> bool:
        """Check if the CLI is properly configured."""
        return bool(self.api_url and self.api_key)

    def show(self) -> dict:
        """Return configuration (with masked API key)."""
        return {
            "api_url": self.api_url,
            "api_key": f"***{self.api_key[-8:]}" if self.api_key else None,
            "default_campaign": self.default_campaign,
            "config_file": str(CONFIG_FILE),
        }


config = Config()
