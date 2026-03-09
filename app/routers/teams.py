"""
Teams API – read-only dataset resource.
GET /teams (paginated list), GET /teams/{team_id} (detail).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.team import TeamResponse
from app.services import team_service

router = APIRouter()


@router.get(
    "/",
    response_model=PaginatedResponse[TeamResponse],
    summary="List teams",
    description="Paginated list of teams (top-5 leagues).",
)
def list_teams(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
) -> PaginatedResponse[TeamResponse]:
    rows, total_count = team_service.get_teams(db, page=page, limit=limit)
    total_pages = (total_count + limit - 1) // limit if total_count else 0
    return PaginatedResponse(
        data=[TeamResponse.model_validate(t) for t in rows],
        page=page,
        total_pages=total_pages,
        total_count=total_count,
    )


@router.get(
    "/{team_id}",
    response_model=TeamResponse,
    summary="Get team by ID",
    description="Single team by club_id; 404 if not found.",
)
def get_team(
    team_id: int,
    db: Session = Depends(get_db),
) -> TeamResponse:
    team = team_service.get_team_by_id(db, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail={"message": "Team not found", "code": "not_found"})
    return TeamResponse.model_validate(team)
