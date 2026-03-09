"""
Tests for X-API-Key authentication: 401 when missing or invalid.
Endpoints under /api/v1 require valid API key.
"""

import pytest
from fastapi.testclient import TestClient


def test_health_no_auth_required(client: TestClient) -> None:
    """Health check does not require API key."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_api_v1_requires_api_key(client: TestClient) -> None:
    """Calling /api/v1 without X-API-Key returns 401 with consistent JSON."""
    r = client.get("/api/v1")
    assert r.status_code == 401
    data = r.json()
    assert "detail" in data
    assert data["detail"].get("code") == "invalid_api_key"
    assert "invalid" in data["detail"].get("message", "").lower() or "missing" in data["detail"].get("message", "").lower()


def test_api_v1_rejects_invalid_api_key(client: TestClient) -> None:
    """Calling /api/v1 with wrong X-API-Key returns 401."""
    r = client.get("/api/v1", headers={"X-API-Key": "wrong-key"})
    assert r.status_code == 401
    assert r.json()["detail"].get("code") == "invalid_api_key"


def test_api_v1_accepts_valid_api_key(client: TestClient, auth_headers: dict) -> None:
    """With valid X-API-Key, /api/v1 returns 200 (not 401)."""
    r = client.get("/api/v1", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == {"api": "v1"}
