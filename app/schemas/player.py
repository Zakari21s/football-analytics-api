"""Player request/response schemas."""

from datetime import date

from pydantic import BaseModel, ConfigDict


class PlayerBase(BaseModel):
    """Shared player fields."""

    player_id: int
    player_name: str
    date_of_birth: date | None = None
    position: str | None = None
    main_position: str | None = None
    current_club_id: int | None = None
    height: float | None = None
    citizenship: str | None = None
    foot: str | None = None
    player_image_url: str | None = None
    current_club_name: str | None = None


class PlayerResponse(PlayerBase):
    """Player for API response. Optional computed fields for list view."""

    model_config = ConfigDict(from_attributes=True)

    age: int | None = None  # computed from date_of_birth (today - dob)
    market_value: float | None = None  # latest value from player_market_value
    minutes_played: float | None = None  # sum across player_performances (respecting filters)
    total_goals: float | None = None
    total_assists: int | None = None
    total_cards: int | None = None
    total_clean_sheets: int | None = None
