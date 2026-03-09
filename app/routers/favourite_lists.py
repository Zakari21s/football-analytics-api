"""
Favourite lists API – main CRUD resource.
POST / (create), GET / (list), GET /{id} (one), PATCH /{id} (update), DELETE /{id} (delete).
"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.favourite_list import (
    FavouriteListAddPlayer,
    FavouriteListCreate,
    FavouriteListResponse,
    FavouriteListUpdate,
)
from app.schemas.player import PlayerResponse
from app.services import favourite_list_service

router = APIRouter()

ListSortBy = Literal["age", "name", "market_value", "minutes_played"]
ListOrder = Literal["asc", "desc"]


@router.post(
    "/",
    response_model=FavouriteListResponse,
    status_code=201,
    summary="Create favourite list",
    description="Create a new favourite list. Returns 201 with the created resource.",
)
def create_favourite_list(
    body: FavouriteListCreate,
    db: Session = Depends(get_db),
) -> FavouriteListResponse:
    obj = favourite_list_service.create_list(db, body.name)
    return FavouriteListResponse.model_validate(obj)


@router.get(
    "/",
    response_model=list[FavouriteListResponse],
    summary="List favourite lists",
    description="Return all favourite lists.",
)
def list_favourite_lists(db: Session = Depends(get_db)) -> list[FavouriteListResponse]:
    rows = favourite_list_service.get_all_lists(db)
    return [FavouriteListResponse.model_validate(r) for r in rows]


@router.get(
    "/{list_id}",
    response_model=FavouriteListResponse,
    summary="Get favourite list by ID",
    description="Single list; 404 if not found.",
)
def get_favourite_list(
    list_id: int,
    db: Session = Depends(get_db),
) -> FavouriteListResponse:
    obj = favourite_list_service.get_list_by_id(db, list_id)
    if obj is None:
        raise HTTPException(status_code=404, detail={"message": "Favourite list not found", "code": "not_found"})
    return FavouriteListResponse.model_validate(obj)


@router.patch(
    "/{list_id}",
    response_model=FavouriteListResponse,
    summary="Update favourite list",
    description="Partial update (e.g. name). 404 if not found.",
)
def update_favourite_list(
    list_id: int,
    body: FavouriteListUpdate,
    db: Session = Depends(get_db),
) -> FavouriteListResponse:
    obj = favourite_list_service.update_list(db, list_id, body.name)
    if obj is None:
        raise HTTPException(status_code=404, detail={"message": "Favourite list not found", "code": "not_found"})
    return FavouriteListResponse.model_validate(obj)


@router.delete(
    "/{list_id}",
    status_code=204,
    summary="Delete favourite list",
    description="Delete a list. 204 No Content; 404 if not found.",
)
def delete_favourite_list(
    list_id: int,
    db: Session = Depends(get_db),
) -> None:
    deleted = favourite_list_service.delete_list(db, list_id)
    if not deleted:
        raise HTTPException(status_code=404, detail={"message": "Favourite list not found", "code": "not_found"})


@router.get(
    "/{list_id}/players",
    response_model=list[PlayerResponse],
    summary="List players in favourite list",
    description="Players in the list with optional sort_by (age, name, market_value, minutes_played) and order (asc/desc). 404 if list not found.",
)
def list_favourite_list_players(
    list_id: int,
    db: Session = Depends(get_db),
    sort_by: ListSortBy = Query("name", description="Sort field"),
    order: ListOrder = Query("asc", description="Sort order"),
) -> list[PlayerResponse]:
    if favourite_list_service.get_list_by_id(db, list_id) is None:
        raise HTTPException(status_code=404, detail={"message": "Favourite list not found", "code": "not_found"})
    data = favourite_list_service.get_players_in_list(db, list_id, sort_by=sort_by, order=order)
    return [PlayerResponse(**d) for d in data]


@router.post(
    "/{list_id}/players",
    status_code=201,
    summary="Add player to favourite list",
    description="Add a player to the list. Body: { \"player_id\": int }. 201 on success; 409 if already in list; 404 if list or player not found.",
)
def add_player_to_favourite_list(
    list_id: int,
    body: FavouriteListAddPlayer,
    db: Session = Depends(get_db),
) -> None:
    result = favourite_list_service.add_player_to_list(db, list_id, body.player_id)
    if result == "not_found_list":
        raise HTTPException(status_code=404, detail={"message": "Favourite list not found", "code": "not_found"})
    if result == "not_found_player":
        raise HTTPException(status_code=404, detail={"message": "Player not found", "code": "not_found"})
    if result == "conflict":
        raise HTTPException(
            status_code=409,
            detail={"message": "Player already in list", "code": "already_in_list"},
        )
    # result == "created"
    return None


@router.delete(
    "/{list_id}/players/{player_id}",
    status_code=204,
    summary="Remove player from favourite list",
    description="Remove a player from the list. 204 No Content; 404 if list or link not found.",
)
def remove_player_from_favourite_list(
    list_id: int,
    player_id: int,
    db: Session = Depends(get_db),
) -> None:
    if favourite_list_service.get_list_by_id(db, list_id) is None:
        raise HTTPException(status_code=404, detail={"message": "Favourite list not found", "code": "not_found"})
    removed = favourite_list_service.remove_player_from_list(db, list_id, player_id)
    if not removed:
        raise HTTPException(
            status_code=404,
            detail={"message": "Player not in list or not found", "code": "not_found"},
        )
    return None
