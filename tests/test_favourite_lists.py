"""
Tests for favourite lists CRUD and list players (add/remove, sort_by).
Full cycle: create → get → patch → add player → get players → remove player → delete.
Endpoints to be implemented.
"""

import pytest
from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    """Sanity: health endpoint is reachable."""
    r = client.get("/health")
    assert r.status_code == 200


# Add CRUD and list-players tests when endpoints are implemented
