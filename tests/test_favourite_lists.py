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


def test_favourite_lists_create(client: TestClient, auth_headers: dict) -> None:
    r = client.post("/api/v1/favourite-lists", json={"name": "Test List"}, headers=auth_headers)
    assert r.status_code == 201
    j = r.json()
    assert "id" in j and j["name"] == "Test List" and "created_at" in j


def test_favourite_lists_list(client: TestClient, auth_headers: dict) -> None:
    r = client.get("/api/v1/favourite-lists", headers=auth_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_favourite_lists_full_crud_cycle(client: TestClient, auth_headers: dict) -> None:
    r = client.post("/api/v1/favourite-lists", json={"name": "CRUD List"}, headers=auth_headers)
    assert r.status_code == 201
    list_id = r.json()["id"]
    r2 = client.get(f"/api/v1/favourite-lists/{list_id}", headers=auth_headers)
    assert r2.status_code == 200
    assert r2.json()["name"] == "CRUD List"
    r3 = client.patch(f"/api/v1/favourite-lists/{list_id}", json={"name": "Updated Name"}, headers=auth_headers)
    assert r3.status_code == 200
    assert r3.json()["name"] == "Updated Name"
    r4 = client.delete(f"/api/v1/favourite-lists/{list_id}", headers=auth_headers)
    assert r4.status_code == 204
    r5 = client.get(f"/api/v1/favourite-lists/{list_id}", headers=auth_headers)
    assert r5.status_code == 404


def test_favourite_lists_get_404(client: TestClient, auth_headers: dict) -> None:
    r = client.get("/api/v1/favourite-lists/999999", headers=auth_headers)
    assert r.status_code == 404


def test_favourite_lists_patch_404(client: TestClient, auth_headers: dict) -> None:
    r = client.patch("/api/v1/favourite-lists/999999", json={"name": "X"}, headers=auth_headers)
    assert r.status_code == 404


def test_favourite_lists_delete_404(client: TestClient, auth_headers: dict) -> None:
    r = client.delete("/api/v1/favourite-lists/999999", headers=auth_headers)
    assert r.status_code == 404


def test_favourite_list_players_add_remove_list(client: TestClient, auth_headers: dict) -> None:
    r = client.post("/api/v1/favourite-lists", json={"name": "PList"}, headers=auth_headers)
    assert r.status_code == 201
    list_id = r.json()["id"]
    r2 = client.get("/api/v1/players?limit=1", headers=auth_headers)
    if not r2.json()["data"]:
        pytest.skip("no players")
    player_id = r2.json()["data"][0]["player_id"]
    r3 = client.post(f"/api/v1/favourite-lists/{list_id}/players", json={"player_id": player_id}, headers=auth_headers)
    assert r3.status_code == 201
    r4 = client.get(f"/api/v1/favourite-lists/{list_id}/players", headers=auth_headers)
    assert r4.status_code == 200
    assert len(r4.json()) == 1
    assert r4.json()[0]["player_id"] == player_id
    r5 = client.post(f"/api/v1/favourite-lists/{list_id}/players", json={"player_id": player_id}, headers=auth_headers)
    assert r5.status_code == 409
    r6 = client.delete(f"/api/v1/favourite-lists/{list_id}/players/{player_id}", headers=auth_headers)
    assert r6.status_code == 204
    r7 = client.get(f"/api/v1/favourite-lists/{list_id}/players", headers=auth_headers)
    assert r7.status_code == 200
    assert len(r7.json()) == 0


def test_favourite_list_players_404_list(client: TestClient, auth_headers: dict) -> None:
    r = client.get("/api/v1/favourite-lists/999999/players", headers=auth_headers)
    assert r.status_code == 404
    r2 = client.post("/api/v1/favourite-lists/999999/players", json={"player_id": 1}, headers=auth_headers)
    assert r2.status_code == 404


def test_favourite_list_players_sort_by(client: TestClient, auth_headers: dict) -> None:
    r = client.post("/api/v1/favourite-lists", json={"name": "SortList"}, headers=auth_headers)
    assert r.status_code == 201
    list_id = r.json()["id"]
    r2 = client.get(f"/api/v1/favourite-lists/{list_id}/players?sort_by=name&order=asc", headers=auth_headers)
    assert r2.status_code == 200
    assert isinstance(r2.json(), list)


def test_favourite_lists_validation_empty_name(client: TestClient, auth_headers: dict) -> None:
    """Empty name should fail validation (422 from Pydantic)."""
    r = client.post("/api/v1/favourite-lists", json={"name": ""}, headers=auth_headers)
    assert r.status_code == 422


def test_favourite_lists_validation_missing_name(client: TestClient, auth_headers: dict) -> None:
    """Missing name should fail validation (422 from Pydantic)."""
    r = client.post("/api/v1/favourite-lists", json={}, headers=auth_headers)
    assert r.status_code == 422


def test_add_player_invalid_player_id(client: TestClient, auth_headers: dict) -> None:
    """Adding a non-existent player_id should return 404."""
    r = client.post("/api/v1/favourite-lists", json={"name": "InvalidPlayer"}, headers=auth_headers)
    assert r.status_code == 201
    list_id = r.json()["id"]
    r2 = client.post(
        f"/api/v1/favourite-lists/{list_id}/players",
        json={"player_id": 999999999},
        headers=auth_headers,
    )
    assert r2.status_code == 404
