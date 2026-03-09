"""
Players API – read-only dataset resource.
GET /players (list with pagination, sort_by, order), GET /players/{player_id} (detail).
"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.performance import PlayerPerformanceResponse
from app.schemas.player import PlayerResponse
from app.schemas.transfer import TransferHistoryResponse
from app.services import player_service

router = APIRouter()

SortBy = Literal["age", "name", "market_value", "minutes_played"]
Order = Literal["asc", "desc"]


@router.get(
    "/",
    response_model=PaginatedResponse[PlayerResponse],
    summary="List players",
    description="Paginated list of players. Sort by age, name, market_value (latest), or minutes_played (total).",
)
def list_players(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    sort_by: SortBy = Query("name", description="Sort field"),
    order: Order = Query("asc", description="Sort order"),
) -> PaginatedResponse[PlayerResponse]:
    data, total_count = player_service.get_players(db, page=page, limit=limit, sort_by=sort_by, order=order)
    total_pages = (total_count + limit - 1) // limit if total_count else 0
    return PaginatedResponse(
        data=[PlayerResponse(**d) for d in data],
        page=page,
        total_pages=total_pages,
        total_count=total_count,
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
    rows, total_count = player_service.get_performances_by_player_id(db, player_id, page=page, limit=limit)
    total_pages = (total_count + limit - 1) // limit if total_count else 0
    return PaginatedResponse(
        data=[PlayerPerformanceResponse.model_validate(r) for r in rows],
        page=page,
        total_pages=total_pages,
        total_count=total_count,
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
    rows, total_count = player_service.get_transfers_by_player_id(db, player_id, page=page, limit=limit)
    total_pages = (total_count + limit - 1) // limit if total_count else 0
    return PaginatedResponse(
        data=[TransferHistoryResponse.model_validate(r) for r in rows],
        page=page,
        total_pages=total_pages,
        total_count=total_count,
    )


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
