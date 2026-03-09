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


def test_teams_list_requires_auth(client: TestClient) -> None:
    r = client.get("/api/v1/teams")
    assert r.status_code == 401


def test_teams_list_pagination(client: TestClient, auth_headers: dict) -> None:
    r = client.get("/api/v1/teams?page=1&limit=5", headers=auth_headers)
    assert r.status_code == 200
    j = r.json()
    assert "data" in j and "page" in j and "total_pages" in j and "total_count" in j
    assert j["page"] == 1
    assert len(j["data"]) <= 5


def test_teams_get_by_id_ok(client: TestClient, auth_headers: dict) -> None:
    r = client.get("/api/v1/teams?limit=1", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()["data"]
    if not data:
        pytest.skip("no teams in DB")
    tid = data[0]["club_id"]
    r2 = client.get(f"/api/v1/teams/{tid}", headers=auth_headers)
    assert r2.status_code == 200
    assert r2.json()["club_id"] == tid


def test_teams_get_by_id_404(client: TestClient, auth_headers: dict) -> None:
    r = client.get("/api/v1/teams/999999999", headers=auth_headers)
    assert r.status_code == 404
