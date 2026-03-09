"""
Tests for teams API (GET list, GET by id).
Endpoints to be implemented.
"""

import pytest
from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    """Sanity: health endpoint is reachable."""
    r = client.get("/health")
    assert r.status_code == 200


# Add tests for GET /api/v1/teams, GET /api/v1/teams/{id} when implemented
