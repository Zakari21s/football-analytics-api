"""
Pytest fixtures: test client, db session, API key for authenticated requests.
Uses in-memory SQLite; optional minimal seed (one player, one team) for tests that need data.
"""

import os
from collections.abc import Generator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure app is importable (run tests from project root or set PYTHONPATH)
os.environ.setdefault("API_KEY", "test-api-key")

from app.database import Base, get_db
from app.main import app as fastapi_app

# Import models so they are registered with Base before create_all
import app.models  # noqa: F401


# ---- In-memory test database ----

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine():
    """Create in-memory SQLite engine once per test session (StaticPool so all connections share one DB)."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    return engine


@pytest.fixture(scope="session")
def test_session_factory(test_engine):
    """Create tables and return a session factory bound to the test engine."""
    Base.metadata.create_all(bind=test_engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db(session_factory: sessionmaker) -> Generator[Session, None, None]:
    """Yield a DB session from the test session factory (used per request)."""
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(
    test_session_factory: sessionmaker, seed_minimal_data: None
) -> Generator[TestClient, None, None]:
    """FastAPI test client using the in-memory DB (get_db overridden), with minimal seed data."""
    def _get_db():
        yield from override_get_db(test_session_factory)

    fastapi_app.dependency_overrides[get_db] = _get_db
    try:
        yield TestClient(fastapi_app)
    finally:
        fastapi_app.dependency_overrides.clear()


@pytest.fixture
def seed_minimal_data(test_session_factory: sessionmaker) -> None:
    """Insert one team and one player (and minimal related rows) so some tests have data."""
    db = test_session_factory()
    try:
        from app.models.models import Player, PlayerMarketValue, PlayerPerformance, Team

        if db.query(Team).first() is not None:
            return  # already seeded (e.g. same session)
        db.add(
            Team(
                club_id=1,
                club_name="Test Club",
                country_name="Test Country",
                competition_id="GB1",
                competition_name="Test League",
                season_id="2023",
            )
        )
        db.add(
            Player(
                player_id=1,
                player_name="Test Player",
                current_club_id=1,
                date_of_birth=date(2000, 1, 15),
                position="Midfielder",
            )
        )
        db.add(
            PlayerPerformance(
                player_id=1,
                season_name="2023",
                competition_id="GB1",
                competition_name="Test League",
                team_id=1,
                goals=5.0,
                assists=3,
                minutes_played=900.0,
            )
        )
        db.add(
            PlayerMarketValue(
                player_id=1,
                date_unix=date(2024, 1, 1),
                value=1_000_000.0,
            )
        )
        db.commit()
    finally:
        db.close()


@pytest.fixture
def api_key() -> str:
    """Valid API key for authenticated requests."""
    return os.environ.get("API_KEY", "test-api-key")


@pytest.fixture
def auth_headers(api_key: str) -> dict:
    """Headers with valid X-API-Key for authenticated tests."""
    return {"X-API-Key": api_key}
