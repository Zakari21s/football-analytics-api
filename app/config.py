"""
Application configuration loaded from environment variables.
No secrets in code; use .env and .env.example for documentation.
"""

import os
from pathlib import Path


def _get_env(key: str, default: str | None = None) -> str | None:
    """Read from environment; optional default."""
    return os.environ.get(key, default)


# Database (SQLite for dev; use env for production)
DATABASE_URL: str = _get_env("DATABASE_URL") or "sqlite:///./football_analytics.db"

# API key for X-API-Key authentication
API_KEY: str | None = _get_env("API_KEY")

# Optional: project root (for resolving paths)
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
