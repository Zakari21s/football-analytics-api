"""Favourite list request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FavouriteListCreate(BaseModel):
    """Body for creating a favourite list."""

    name: str = Field(..., min_length=1, max_length=255)


class FavouriteListUpdate(BaseModel):
    """Body for PATCH (partial update); all fields optional."""

    name: str | None = Field(None, min_length=1, max_length=255)


class FavouriteListResponse(BaseModel):
    """Favourite list in API response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime


class FavouriteListAddPlayer(BaseModel):
    """Body for adding a player to a list."""

    player_id: int
