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


def test_players_list_requires_auth(client: TestClient) -> None:
    r = client.get("/api/v1/players")
    assert r.status_code == 401


def test_players_list_pagination(client: TestClient, auth_headers: dict) -> None:
    r = client.get("/api/v1/players?page=1&limit=5", headers=auth_headers)
    assert r.status_code == 200
    j = r.json()
    assert "data" in j and "page" in j and "total_pages" in j and "total_count" in j
    assert j["page"] == 1
    assert len(j["data"]) <= 5
    assert j["total_count"] >= 0


def test_players_list_sort_by(client: TestClient, auth_headers: dict) -> None:
    r = client.get("/api/v1/players?limit=3&sort_by=name&order=asc", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()["data"]
    if len(data) >= 2:
        names = [p["player_name"] for p in data]
        assert names == sorted(names)


def test_players_get_by_id_ok(client: TestClient, auth_headers: dict) -> None:
    r = client.get("/api/v1/players?limit=1", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()["data"]
    if not data:
        pytest.skip("no players in DB")
    pid = data[0]["player_id"]
    r2 = client.get(f"/api/v1/players/{pid}", headers=auth_headers)
    assert r2.status_code == 200
    assert r2.json()["player_id"] == pid


def test_players_get_by_id_404(client: TestClient, auth_headers: dict) -> None:
    r = client.get("/api/v1/players/999999999", headers=auth_headers)
    assert r.status_code == 404


def test_players_performances_404_if_player_missing(client: TestClient, auth_headers: dict) -> None:
    r = client.get("/api/v1/players/999999999/performances", headers=auth_headers)
    assert r.status_code == 404


def test_players_performances_pagination(client: TestClient, auth_headers: dict) -> None:
    r = client.get("/api/v1/players?limit=1", headers=auth_headers)
    if r.status_code != 200 or not r.json()["data"]:
        pytest.skip("no players")
    pid = r.json()["data"][0]["player_id"]
    r2 = client.get(f"/api/v1/players/{pid}/performances?page=1&limit=5", headers=auth_headers)
    assert r2.status_code == 200
    j = r2.json()
    assert "data" in j and "total_count" in j


def test_players_transfers_404_if_player_missing(client: TestClient, auth_headers: dict) -> None:
    r = client.get("/api/v1/players/999999999/transfers", headers=auth_headers)
    assert r.status_code == 404


def test_players_transfers_pagination(client: TestClient, auth_headers: dict) -> None:
    r = client.get("/api/v1/players?limit=1", headers=auth_headers)
    if r.status_code != 200 or not r.json()["data"]:
        pytest.skip("no players")
    pid = r.json()["data"][0]["player_id"]
    r2 = client.get(f"/api/v1/players/{pid}/transfers?page=1&limit=5", headers=auth_headers)
    assert r2.status_code == 200
    j = r2.json()
    assert "data" in j and "total_count" in j


def test_player_details_ok(client: TestClient, auth_headers: dict) -> None:
    """GET /players?limit=1 → take first player_id → GET /players/{id}/details → 200 and expected keys."""
    r = client.get("/api/v1/players?limit=1", headers=auth_headers)
    assert r.status_code == 200
    data = r.json().get("data") or []
    if not data:
        pytest.skip("no players in DB")
    player_id = data[0]["player_id"]
    r2 = client.get(f"/api/v1/players/{player_id}/details", headers=auth_headers)
    assert r2.status_code == 200
    body = r2.json()
    assert body.get("player_id") == player_id
    assert "player_name" in body
    assert "current_market_value" in body
    assert "market_value_history" in body
    assert isinstance(body["market_value_history"], list)
    assert "career" in body
    career = body["career"]
    assert "seasons_played" in career
    assert "previous_clubs" in career
    assert isinstance(career["previous_clubs"], list)
    for entry in career["previous_clubs"]:
        assert "club_name" in entry
        assert isinstance(entry["club_name"], str)


def test_player_details_404(client: TestClient, auth_headers: dict) -> None:
    """GET /players/999999999/details → 404."""
    r = client.get("/api/v1/players/999999999/details", headers=auth_headers)
    assert r.status_code == 404
