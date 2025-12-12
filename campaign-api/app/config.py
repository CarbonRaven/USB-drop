"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_url: str = "postgresql://usbdrop:password@localhost:5432/usbdrop"

    # CanaryTokens
    canary_server: str = "http://localhost:8082"
    canary_domain: str = "subproject55.com"
    factory_auth: str = ""

    # OpenAI
    openai_api_key: str = ""

    # Slack
    slack_webhook_url: str = ""

    # JWT Authentication
    jwt_secret_key: str = "change-this-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # Initial Admin User
    admin_username: str = "admin"
    admin_email: str = "admin@example.com"
    admin_password: str = "change-this-password"

    # Application
    app_name: str = "USB Drop Campaign Manager"
    debug: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
