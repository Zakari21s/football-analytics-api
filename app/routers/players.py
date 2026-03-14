"""
Players API – read-only dataset resource.
GET /players (list with pagination, sort_by, order), GET /players/{player_id} (detail).
"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import PaginatedResponse, build_paginated_response
from app.schemas.performance import PlayerPerformanceResponse
from app.schemas.player import PlayerDetailsResponse, PlayerResponse
from app.schemas.transfer import TransferHistoryResponse
from app.services import player_service

router = APIRouter()

SortBy = Literal[
    "name",
    "age",
    "position",
    "foot",
    "market_value",
    "minutes_played",
    "goals",
    "assists",
    "cards",
    "clean_sheets",
]
Order = Literal["asc", "desc"]


@router.get(
    "/",
    response_model=PaginatedResponse[PlayerResponse],
    summary="List players",
    description=(
        "Paginated list of players. Optional filter by league (competition_id) and season. "
        "Sort by name, age, position, foot, market_value (latest), minutes_played (filtered), "
        "assists, cards, or clean_sheets (keepers)."
    ),
)
def list_players(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    sort_by: SortBy = Query("name", description="Sort field"),
    order: Order = Query("asc", description="Sort order"),
    search: str | None = Query(None, description="Filter by player name (partial match)"),
    competition_id: str | None = Query(None, description="Filter by league (e.g. GB1, ES1)"),
    season: str | None = Query(None, description="Filter by season (e.g. 2023, 08/09)"),
) -> PaginatedResponse[PlayerResponse]:
    data, total_count = player_service.get_players(
        db, page=page, limit=limit, sort_by=sort_by, order=order,
        search=search, competition_id=competition_id, season=season,
    )
    return build_paginated_response(
        data=[PlayerResponse(**d) for d in data],
        total_count=total_count,
        page=page,
        limit=limit,
    )


@router.get(
    "/{player_id}/performances",
    response_model=PaginatedResponse[PlayerPerformanceResponse],
    summary="List player performances",
    description="Paginated list of performances (season/competition/team) for a player. 404 if player not found.",
)
def list_player_performances(
    player_id: int,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
) -> PaginatedResponse[PlayerPerformanceResponse]:
    if player_service.get_player_by_id(db, player_id) is None:
        raise HTTPException(status_code=404, detail={"message": "Player not found", "code": "not_found"})
    rows, total_count = player_service.get_performances_by_player_id(
        db, player_id, page=page, limit=limit
    )
    return build_paginated_response(
        data=[PlayerPerformanceResponse.model_validate(r) for r in rows],
        total_count=total_count,
        page=page,
        limit=limit,
    )


@router.get(
    "/{player_id}/transfers",
    response_model=PaginatedResponse[TransferHistoryResponse],
    summary="List player transfers",
    description="Paginated transfer history for a player. 404 if player not found.",
)
def list_player_transfers(
    player_id: int,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
) -> PaginatedResponse[TransferHistoryResponse]:
    if player_service.get_player_by_id(db, player_id) is None:
        raise HTTPException(status_code=404, detail={"message": "Player not found", "code": "not_found"})
    rows, total_count = player_service.get_transfers_by_player_id(
        db, player_id, page=page, limit=limit
    )
    return build_paginated_response(
        data=[TransferHistoryResponse.model_validate(r) for r in rows],
        total_count=total_count,
        page=page,
        limit=limit,
    )


@router.get(
    "/{player_id}/details",
    response_model=PlayerDetailsResponse,
    summary="Get rich player details",
    description=(
        "Player profile with current market value, historical market value points, "
        "and a compact career summary (seasons played, previous clubs). 404 if player not found."
    ),
)
def get_player_details(
    player_id: int,
    db: Session = Depends(get_db),
) -> PlayerDetailsResponse:
    details = player_service.get_player_details(db, player_id)
    if details is None:
        raise HTTPException(
            status_code=404,
            detail={"message": "Player not found", "code": "not_found"},
        )
    return PlayerDetailsResponse(**details)


@router.get(
    "/{player_id}",
    response_model=PlayerResponse,
    summary="Get player by ID",
    description="Single player; 404 if not found.",
)
def get_player(
    player_id: int,
    db: Session = Depends(get_db),
) -> PlayerResponse:
    player = player_service.get_player_by_id(db, player_id)
    if player is None:
        raise HTTPException(status_code=404, detail={"message": "Player not found", "code": "not_found"})
    return PlayerResponse(**player_service.player_to_response_dict(player, db=db))
