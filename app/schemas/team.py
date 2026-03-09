"""Team request/response schemas."""

from pydantic import BaseModel, ConfigDict


class TeamResponse(BaseModel):
    """Team for API response (read-only dataset)."""

    model_config = ConfigDict(from_attributes=True)

    club_id: int
    club_name: str
    country_name: str | None = None
    competition_id: str | None = None
    competition_name: str | None = None
    season_id: str | None = None
