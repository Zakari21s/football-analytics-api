"""Schema for season list."""

from pydantic import BaseModel


class SeasonResponse(BaseModel):
    """Single season for dropdowns."""

    season_name: str
