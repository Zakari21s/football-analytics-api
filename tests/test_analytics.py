"""
Tests for analytics API: top-scorers, top-market-values, most-minutes-played.
"""

import pytest
from fastapi.testclient import TestClient


def test_analytics_requires_auth(client: TestClient) -> None:
    r = client.get("/api/v1/analytics/top-scorers")
    assert r.status_code == 401


def test_top_scorers(client: TestClient, auth_headers: dict) -> None:
    r = client.get("/api/v1/analytics/top-scorers?limit=5", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    if data:
        assert "player_id" in data[0] and "player_name" in data[0] and "total_goals" in data[0]
        # Should be descending by goals
        goals = [x["total_goals"] for x in data]
        assert goals == sorted(goals, reverse=True)


def test_top_market_values(client: TestClient, auth_headers: dict) -> None:
    r = client.get("/api/v1/analytics/top-market-values?limit=5", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    if data:
        assert "player_id" in data[0] and "player_name" in data[0] and "market_value" in data[0]
        values = [x["market_value"] for x in data]
        assert values == sorted(values, reverse=True)


def test_most_minutes_played(client: TestClient, auth_headers: dict) -> None:
    r = client.get("/api/v1/analytics/most-minutes-played?limit=5", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    if data:
        assert "player_id" in data[0] and "player_name" in data[0] and "total_minutes" in data[0]
        minutes = [x["total_minutes"] for x in data]
        assert minutes == sorted(minutes, reverse=True)


def test_top_scorers_with_filters(client: TestClient, auth_headers: dict) -> None:
    r = client.get(
        "/api/v1/analytics/top-scorers?season=08/09&competition_id=GB1&limit=3",
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_top_assists(client: TestClient, auth_headers: dict) -> None:
    """GET /analytics/top-assists?limit=5 → 200, list; if non-empty check keys and descending assists."""
    r = client.get("/api/v1/analytics/top-assists?limit=5", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    if data:
        first = data[0]
        assert "player_id" in first and "player_name" in first and "total_assists" in first
        assists = [x["total_assists"] for x in data]
        assert assists == sorted(assists, reverse=True)


def test_youngest_stars(client: TestClient, auth_headers: dict) -> None:
    """GET /analytics/youngest-stars?limit=5 → 200, list; if non-empty check first item keys."""
    r = client.get("/api/v1/analytics/youngest-stars?limit=5", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    if data:
        first = data[0]
        assert "player_id" in first and "player_name" in first
        assert "age" in first and "total_minutes" in first and "total_goals" in first
