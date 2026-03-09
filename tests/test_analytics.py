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
