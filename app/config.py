"""
Application configuration loaded from environment variables.
Uses pydantic-settings for validation and .env support. No secrets in code.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings loaded from environment and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///./football_analytics.db"
    api_key: str | None = None

    @property
    def project_root(self) -> Path:
        """Project root (parent of app/)."""
        return Path(__file__).resolve().parent.parent


# Singleton for use in database.py, auth, etc.
settings = Settings()
