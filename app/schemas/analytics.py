"""Analytics API response schemas."""

from pydantic import BaseModel


class TopScorerResponse(BaseModel):
    """Player with total goals (aggregated from performances)."""

    player_id: int
    player_name: str
    total_goals: float


class TopMarketValueResponse(BaseModel):
    """Player with latest market value."""

    player_id: int
    player_name: str
    market_value: float


class MostMinutesPlayedResponse(BaseModel):
    """Player with total minutes played (aggregated from performances)."""

    player_id: int
    player_name: str
    total_minutes: float
