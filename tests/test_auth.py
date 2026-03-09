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


# Add tests for 401 on missing X-API-Key and invalid key when v1 routes are protected and implemented
