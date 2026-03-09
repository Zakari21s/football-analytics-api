"""Transfer history response schema (read-only, from transfer_history)."""

from datetime import date

from pydantic import BaseModel, ConfigDict


class TransferHistoryResponse(BaseModel):
    """Single transfer record for a player."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    player_id: int
    season_name: str | None = None
    transfer_date: date | None = None
    from_team_id: int | None = None
    to_team_id: int | None = None
    transfer_type: str | None = None
    value_at_transfer: float | None = None
    transfer_fee: float | None = None
