"""Schema for competition (league) list."""

from pydantic import BaseModel


class CompetitionResponse(BaseModel):
    """Single competition/league for dropdowns."""

    competition_id: str
    competition_name: str
