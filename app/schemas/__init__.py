"""
Pydantic request/response schemas for API validation and serialisation.
"""

from app.schemas.analytics import (
    MostMinutesPlayedResponse,
    TopMarketValueResponse,
    TopScorerResponse,
)
from app.schemas.common import PaginatedResponse
from app.schemas.favourite_list import (
    FavouriteListAddPlayer,
    FavouriteListCreate,
    FavouriteListResponse,
    FavouriteListUpdate,
)
from app.schemas.performance import PlayerPerformanceResponse
from app.schemas.player import PlayerResponse
from app.schemas.team import TeamResponse
from app.schemas.transfer import TransferHistoryResponse

__all__ = [
    "FavouriteListAddPlayer",
    "MostMinutesPlayedResponse",
    "TopMarketValueResponse",
    "TopScorerResponse",
    "FavouriteListCreate",
    "FavouriteListResponse",
    "FavouriteListUpdate",
    "PaginatedResponse",
    "PlayerPerformanceResponse",
    "PlayerResponse",
    "TeamResponse",
    "TransferHistoryResponse",
]
