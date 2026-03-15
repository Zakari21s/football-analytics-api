"""
SQLAlchemy models for dataset tables (read-only from API) and application tables (FavouriteList CRUD).
Match ERD and CSV column mapping from project plan section 3.1.
"""

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Date, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.models import Team


# ---- Dataset models (read-only from API) ----


class Player(Base):
    """From player_profiles CSV. player_id PK; current_club_id FK → teams.club_id."""

    __tablename__ = "players"

    player_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_slug: Mapped[str | None] = mapped_column(String(255), nullable=True)
    player_name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    position: Mapped[str | None] = mapped_column(String(128), nullable=True)
    main_position: Mapped[str | None] = mapped_column(String(64), nullable=True)
    foot: Mapped[str | None] = mapped_column(String(16), nullable=True)
    player_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    current_club_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("teams.club_id"), nullable=True
    )
    height: Mapped[float | None] = mapped_column(Float, nullable=True)
    citizenship: Mapped[str | None] = mapped_column(String(128), nullable=True)

    current_club: Mapped["Team | None"] = relationship(
        "Team", back_populates="players", foreign_keys=[current_club_id]
    )
    performances: Mapped[list["PlayerPerformance"]] = relationship(
        "PlayerPerformance", back_populates="player"
    )
    market_values: Mapped[list["PlayerMarketValue"]] = relationship(
        "PlayerMarketValue", back_populates="player"
    )


class Team(Base):
    """From team_details CSV; deduplicated by club_id (one row per club)."""

    __tablename__ = "teams"

    club_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    club_name: Mapped[str] = mapped_column(String(255), nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    country_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    competition_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    competition_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    season_id: Mapped[str | None] = mapped_column(String(32), nullable=True)

    players: Mapped[list["Player"]] = relationship(
        "Player", back_populates="current_club", foreign_keys="Player.current_club_id"
    )


class PlayerPerformance(Base):
    """From player_performances CSV. One row per player/season/competition/team."""

    __tablename__ = "player_performances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.player_id"), nullable=False)
    season_name: Mapped[str | None] = mapped_column(String(32), nullable=True)
    competition_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    competition_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    team_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # club_id in CSV
    goals: Mapped[float | None] = mapped_column(Float, nullable=True)
    assists: Mapped[int | None] = mapped_column(Integer, nullable=True)
    minutes_played: Mapped[float | None] = mapped_column(Float, nullable=True)
    yellow_cards: Mapped[int | None] = mapped_column(Integer, nullable=True)
    direct_red_cards: Mapped[int | None] = mapped_column(Integer, nullable=True)
    clean_sheets: Mapped[int | None] = mapped_column(Integer, nullable=True)

    player: Mapped["Player"] = relationship("Player", back_populates="performances")


class TransferHistory(Base):
    """From transfer_history CSV."""

    __tablename__ = "transfer_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.player_id"), nullable=False)
    season_name: Mapped[str | None] = mapped_column(String(32), nullable=True)
    transfer_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    from_team_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    to_team_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    transfer_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    value_at_transfer: Mapped[float | None] = mapped_column(Float, nullable=True)
    transfer_fee: Mapped[float | None] = mapped_column(Float, nullable=True)


class PlayerMarketValue(Base):
    """From player_market_value CSV. Historical values; latest per player = current value."""

    __tablename__ = "player_market_value"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.player_id"), nullable=False)
    date_unix: Mapped[date] = mapped_column(Date, nullable=False)  # CSV has date string e.g. 2023-12-19
    value: Mapped[float] = mapped_column(Float, nullable=False)

    player: Mapped["Player"] = relationship("Player", back_populates="market_values")


# ---- Application models (FavouriteList = main CRUD resource) ----


class FavouriteList(Base):
    """User-created list of favourite players."""

    __tablename__ = "favourite_lists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=lambda: datetime.now(timezone.utc))

    list_players: Mapped[list["FavouriteListPlayer"]] = relationship(
        "FavouriteListPlayer", back_populates="favourite_list", cascade="all, delete-orphan"
    )


class FavouriteListPlayer(Base):
    """Many-to-many: which players are in which list. Unique (list_id, player_id)."""

    __tablename__ = "favourite_list_players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    list_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("favourite_lists.id", ondelete="CASCADE"), nullable=False
    )
    player_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("players.player_id", ondelete="CASCADE"), nullable=False
    )

    __table_args__ = (UniqueConstraint("list_id", "player_id", name="uq_list_player"),)

    favourite_list: Mapped["FavouriteList"] = relationship(
        "FavouriteList", back_populates="list_players"
    )
    player: Mapped["Player"] = relationship("Player")
