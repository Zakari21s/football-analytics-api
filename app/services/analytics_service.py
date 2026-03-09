"""
Analytics service: top-scorers, top-market-values, most-minutes-played.
"""

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models import Player, PlayerMarketValue, PlayerPerformance

DEFAULT_LIMIT = 10
MAX_LIMIT = 100


def get_top_scorers(
    db: Session,
    season: str | None = None,
    competition_id: str | None = None,
    limit: int = DEFAULT_LIMIT,
) -> list[tuple[int, str, float]]:
    """
    Aggregate SUM(goals) per player from player_performances; optional filter by season, competition_id.
    Returns list of (player_id, player_name, total_goals) ordered by total_goals desc.
    """
    limit = min(max(1, limit), MAX_LIMIT)
    sub = (
        select(
            PlayerPerformance.player_id,
            func.coalesce(func.sum(PlayerPerformance.goals), 0).label("total_goals"),
        )
        .where(True)
        .group_by(PlayerPerformance.player_id)
    )
    if season is not None and season.strip():
        sub = sub.where(PlayerPerformance.season_name == season.strip())
    if competition_id is not None and competition_id.strip():
        sub = sub.where(PlayerPerformance.competition_id == competition_id.strip())
    sub = sub.subquery()
    q = (
        select(Player.player_id, Player.player_name, sub.c.total_goals)
        .join(sub, Player.player_id == sub.c.player_id)
        .order_by(sub.c.total_goals.desc())
        .limit(limit)
    )
    rows = db.execute(q).all()
    return [(r.player_id, r.player_name, float(r.total_goals)) for r in rows]


def get_top_market_values(
    db: Session,
    limit: int = DEFAULT_LIMIT,
) -> list[tuple[int, str, float]]:
    """
    Latest market value per player (max date_unix); order by value desc.
    Returns list of (player_id, player_name, market_value).
    """
    limit = min(max(1, limit), MAX_LIMIT)
    sub_max = (
        select(PlayerMarketValue.player_id, func.max(PlayerMarketValue.date_unix).label("max_date"))
        .group_by(PlayerMarketValue.player_id)
        .subquery()
    )
    sub_latest = (
        select(PlayerMarketValue.player_id, PlayerMarketValue.value)
        .join(
            sub_max,
            and_(
                PlayerMarketValue.player_id == sub_max.c.player_id,
                PlayerMarketValue.date_unix == sub_max.c.max_date,
            ),
        )
        .subquery()
    )
    q = (
        select(Player.player_id, Player.player_name, sub_latest.c.value)
        .join(sub_latest, Player.player_id == sub_latest.c.player_id)
        .order_by(sub_latest.c.value.desc())
        .limit(limit)
    )
    rows = db.execute(q).all()
    return [(r.player_id, r.player_name, float(r.value)) for r in rows]


def get_most_minutes_played(
    db: Session,
    season: str | None = None,
    limit: int = DEFAULT_LIMIT,
) -> list[tuple[int, str, float]]:
    """
    Aggregate SUM(minutes_played) per player; optional filter by season.
    Returns list of (player_id, player_name, total_minutes) ordered by total_minutes desc.
    """
    limit = min(max(1, limit), MAX_LIMIT)
    sub = (
        select(
            PlayerPerformance.player_id,
            func.coalesce(func.sum(PlayerPerformance.minutes_played), 0).label("total_minutes"),
        )
        .group_by(PlayerPerformance.player_id)
    )
    if season is not None and season.strip():
        sub = sub.where(PlayerPerformance.season_name == season.strip())
    sub = sub.subquery()
    q = (
        select(Player.player_id, Player.player_name, sub.c.total_minutes)
        .join(sub, Player.player_id == sub.c.player_id)
        .order_by(sub.c.total_minutes.desc())
        .limit(limit)
    )
    rows = db.execute(q).all()
    return [(r.player_id, r.player_name, float(r.total_minutes)) for r in rows]
