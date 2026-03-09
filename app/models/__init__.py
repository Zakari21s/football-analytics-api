"""
SQLAlchemy models: dataset (Player, Team, etc.) and application (FavouriteList, FavouriteListPlayer).
Import this module so all models are registered with Base before create_all().
"""

from app.database import Base
from app.models.models import (
    FavouriteList,
    FavouriteListPlayer,
    Player,
    PlayerMarketValue,
    PlayerPerformance,
    Team,
    TransferHistory,
)

__all__ = [
    "Base",
    "Player",
    "Team",
    "PlayerPerformance",
    "TransferHistory",
    "PlayerMarketValue",
    "FavouriteList",
    "FavouriteListPlayer",
]
