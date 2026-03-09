"""
Pytest fixtures: test client, db session, API key for authenticated requests.
Use in-memory SQLite or test DB; seed minimal data in tests as needed.
"""

import os

import pytest
from fastapi.testclient import TestClient

# Ensure app is importable (run tests from project root or set PYTHONPATH)
os.environ.setdefault("API_KEY", "test-api-key")

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client (no auth by default)."""
    return TestClient(app)


@pytest.fixture
def api_key() -> str:
    """Valid API key for authenticated requests."""
    return os.environ.get("API_KEY", "test-api-key")


@pytest.fixture
def auth_headers(api_key: str) -> dict:
    """Headers with valid X-API-Key for authenticated tests."""
    return {"X-API-Key": api_key}
