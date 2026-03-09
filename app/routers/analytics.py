"""
Analytics API – top-scorers, top-market-values, most-minutes-played.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.analytics import (
    MostMinutesPlayedResponse,
    TopMarketValueResponse,
    TopScorerResponse,
)
from app.services import analytics_service

router = APIRouter()


@router.get(
    "/top-scorers",
    response_model=list[TopScorerResponse],
    summary="Top scorers",
    description="Players with most goals (SUM from performances). Optional filter by season and competition_id. Default limit 10.",
)
def top_scorers(
    db: Session = Depends(get_db),
    season: str | None = Query(None, description="Filter by season (e.g. 2023, 08/09)"),
    competition_id: str | None = Query(None, description="Filter by competition (e.g. GB1, ES1)"),
    limit: int = Query(10, ge=1, le=100, description="Number of results"),
) -> list[TopScorerResponse]:
    rows = analytics_service.get_top_scorers(db, season=season, competition_id=competition_id, limit=limit)
    return [TopScorerResponse(player_id=r[0], player_name=r[1], total_goals=r[2]) for r in rows]


@router.get(
    "/top-market-values",
    response_model=list[TopMarketValueResponse],
    summary="Top market values",
    description="Players with highest latest market value. Uses most recent value per player from player_market_value.",
)
def top_market_values(
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=100, description="Number of results"),
) -> list[TopMarketValueResponse]:
    rows = analytics_service.get_top_market_values(db, limit=limit)
    return [TopMarketValueResponse(player_id=r[0], player_name=r[1], market_value=r[2]) for r in rows]


@router.get(
    "/most-minutes-played",
    response_model=list[MostMinutesPlayedResponse],
    summary="Most minutes played",
    description="Players with most minutes played (SUM from performances). Optional filter by season.",
)
def most_minutes_played(
    db: Session = Depends(get_db),
    season: str | None = Query(None, description="Filter by season"),
    limit: int = Query(10, ge=1, le=100, description="Number of results"),
) -> list[MostMinutesPlayedResponse]:
    rows = analytics_service.get_most_minutes_played(db, season=season, limit=limit)
    return [MostMinutesPlayedResponse(player_id=r[0], player_name=r[1], total_minutes=r[2]) for r in rows]
