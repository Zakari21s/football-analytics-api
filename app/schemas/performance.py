"""Player performance response schema (read-only, from player_performances)."""

from pydantic import BaseModel, ConfigDict


class PlayerPerformanceResponse(BaseModel):
    """One row per player/season/competition/team."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    player_id: int
    season_name: str | None = None
    competition_id: str | None = None
    competition_name: str | None = None
    team_id: int | None = None
    goals: float | None = None
    assists: int | None = None
    minutes_played: float | None = None
    yellow_cards: int | None = None
    direct_red_cards: int | None = None
    clean_sheets: int | None = None
