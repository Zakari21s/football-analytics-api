"""
Player service: list with sort/pagination and get by id.
Sort by age (date_of_birth), name, market_value (latest), minutes_played (sum).
"""

from datetime import date
from typing import Literal

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models import Player, PlayerMarketValue, PlayerPerformance, TransferHistory

SortBy = Literal["age", "name", "market_value", "minutes_played"]
Order = Literal["asc", "desc"]

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


def _age_from_dob(dob: date | None) -> int | None:
    if dob is None:
        return None
    today = date.today()
    return (today - dob).days // 365


def _player_to_response(
    player: Player,
    *,
    latest_value: float | None = None,
    total_minutes: float | None = None,
) -> dict:
    """Build dict for PlayerResponse with optional computed fields."""
    return {
        "player_id": player.player_id,
        "player_name": player.player_name,
        "date_of_birth": player.date_of_birth,
        "position": player.position,
        "main_position": player.main_position,
        "current_club_id": player.current_club_id,
        "height": player.height,
        "citizenship": player.citizenship,
        "age": _age_from_dob(player.date_of_birth),
        "market_value": latest_value,
        "minutes_played": total_minutes,
    }


def get_players(
    db: Session,
    page: int = 1,
    limit: int = DEFAULT_LIMIT,
    sort_by: SortBy = "name",
    order: Order = "asc",
) -> tuple[list[dict], int]:
    """
    List players with pagination and sort.
    Returns (list of player response dicts, total_count).
    """
    limit = min(max(1, limit), MAX_LIMIT)
    page = max(1, page)
    offset = (page - 1) * limit

    # Base query: Player
    q = select(Player)

    if sort_by == "name":
        order_col = Player.player_name
    elif sort_by == "age":
        # asc = oldest first (date_of_birth asc), desc = youngest first (date_of_birth desc)
        order_col = Player.date_of_birth
    elif sort_by == "market_value":
        # Subquery: latest value per player (max date_unix)
        sub_max = (
            select(PlayerMarketValue.player_id, func.max(PlayerMarketValue.date_unix).label("max_date"))
            .group_by(PlayerMarketValue.player_id)
            .subquery()
        )
        sub_latest = (
            select(PlayerMarketValue.player_id, PlayerMarketValue.value)
            .join(sub_max, and_(
                PlayerMarketValue.player_id == sub_max.c.player_id,
                PlayerMarketValue.date_unix == sub_max.c.max_date,
            ))
            .subquery()
        )
        q = q.outerjoin(sub_latest, Player.player_id == sub_latest.c.player_id)
        order_col = sub_latest.c.value
    elif sort_by == "minutes_played":
        # Subquery: sum(minutes_played) per player
        sub_mins = (
            select(
                PlayerPerformance.player_id,
                func.coalesce(func.sum(PlayerPerformance.minutes_played), 0).label("total_minutes"),
            )
            .group_by(PlayerPerformance.player_id)
            .subquery()
        )
        q = q.outerjoin(sub_mins, Player.player_id == sub_mins.c.player_id)
        order_col = sub_mins.c.total_minutes
    else:
        order_col = Player.player_name

    q = q.order_by(order_col.asc() if order == "asc" else order_col.desc())
    count_q = select(func.count()).select_from(Player)
    total_count = db.execute(count_q).scalar() or 0

    q = q.offset(offset).limit(limit)
    rows = db.execute(q).scalars().unique().all()

    # Resolve latest value and total minutes for each player (for response)
    player_ids = [p.player_id for p in rows]
    latest_values: dict[int, float] = {}
    if player_ids:
        sub_max = (
            select(PlayerMarketValue.player_id, func.max(PlayerMarketValue.date_unix).label("md"))
            .where(PlayerMarketValue.player_id.in_(player_ids))
            .group_by(PlayerMarketValue.player_id)
            .subquery()
        )
        mv_rows = (
            db.execute(
                select(PlayerMarketValue.player_id, PlayerMarketValue.value).join(
                    sub_max,
                    and_(
                        PlayerMarketValue.player_id == sub_max.c.player_id,
                        PlayerMarketValue.date_unix == sub_max.c.md,
                    ),
                )
            )
            .all()
        )
        latest_values = {r.player_id: r.value for r in mv_rows}

    total_minutes_map: dict[int, float] = {}
    if player_ids:
        mins_rows = (
            db.execute(
                select(
                    PlayerPerformance.player_id,
                    func.coalesce(func.sum(PlayerPerformance.minutes_played), 0).label("m"),
                )
                .where(PlayerPerformance.player_id.in_(player_ids))
                .group_by(PlayerPerformance.player_id)
            )
            .all()
        )
        total_minutes_map = {r.player_id: float(r.m) for r in mins_rows}

    data = [
        _player_to_response(
            p,
            latest_value=latest_values.get(p.player_id),
            total_minutes=total_minutes_map.get(p.player_id),
        )
        for p in rows
    ]
    return data, total_count


def get_player_by_id(db: Session, player_id: int) -> Player | None:
    """Return one Player by id or None."""
    return db.get(Player, player_id)


def player_to_response_dict(
    player: Player,
    db: Session | None = None,
) -> dict:
    """Build full response dict for one player (with optional market_value, minutes_played)."""
    latest_value: float | None = None
    total_minutes: float | None = None
    if db is not None:
        mv = (
            db.execute(
                select(PlayerMarketValue.value)
                .where(PlayerMarketValue.player_id == player.player_id)
                .order_by(PlayerMarketValue.date_unix.desc())
                .limit(1)
            )
            .scalar()
        )
        if mv is not None:
            latest_value = float(mv)
        mins = (
            db.execute(
                select(func.coalesce(func.sum(PlayerPerformance.minutes_played), 0)).where(
                    PlayerPerformance.player_id == player.player_id
                )
            )
            .scalar()
        )
        if mins is not None:
            total_minutes = float(mins)
    return _player_to_response(player, latest_value=latest_value, total_minutes=total_minutes)


def get_performances_by_player_id(
    db: Session,
    player_id: int,
    page: int = 1,
    limit: int = DEFAULT_LIMIT,
) -> tuple[list[PlayerPerformance], int]:
    """
    List performances for a player (paginated). Returns (list, total_count).
    Does not check if player exists; router should return 404 when player is missing.
    """
    limit = min(max(1, limit), MAX_LIMIT)
    page = max(1, page)
    offset = (page - 1) * limit
    count_q = (
        select(func.count())
        .select_from(PlayerPerformance)
        .where(PlayerPerformance.player_id == player_id)
    )
    total_count = db.execute(count_q).scalar() or 0
    q = (
        select(PlayerPerformance)
        .where(PlayerPerformance.player_id == player_id)
        .order_by(PlayerPerformance.season_name.desc(), PlayerPerformance.id.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = db.execute(q).scalars().unique().all()
    return list(rows), total_count


def get_transfers_by_player_id(
    db: Session,
    player_id: int,
    page: int = 1,
    limit: int = DEFAULT_LIMIT,
) -> tuple[list[TransferHistory], int]:
    """
    List transfer history for a player (paginated). Returns (list, total_count).
    Does not check if player exists; router should return 404 when player is missing.
    """
    limit = min(max(1, limit), MAX_LIMIT)
    page = max(1, page)
    offset = (page - 1) * limit
    count_q = (
        select(func.count())
        .select_from(TransferHistory)
        .where(TransferHistory.player_id == player_id)
    )
    total_count = db.execute(count_q).scalar() or 0
    q = (
        select(TransferHistory)
        .where(TransferHistory.player_id == player_id)
        .order_by(TransferHistory.transfer_date.desc(), TransferHistory.id.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = db.execute(q).scalars().unique().all()
    return list(rows), total_count
