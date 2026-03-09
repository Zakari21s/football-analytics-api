"""
Tests for players API (GET list, GET by id, sorting, pagination).
Endpoints to be implemented.
"""

import pytest
from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    """Sanity: health endpoint is reachable."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# Add tests for GET /api/v1/players, GET /api/v1/players/{id}, sort_by, page, limit when implemented
