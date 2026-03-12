"""
Favourite list service: full CRUD + list players (add, remove, list with sort).
"""

from datetime import date
from typing import Literal

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models import (
    FavouriteList,
    FavouriteListPlayer,
    Player,
    PlayerMarketValue,
    PlayerPerformance,
    Team,
)

ListSortBy = Literal["age", "name", "market_value", "minutes_played"]
ListOrder = Literal["asc", "desc"]


def _age_from_dob(dob: date | None) -> int | None:
    if dob is None:
        return None
    return (date.today() - dob).days // 365


def _player_to_response_dict(
    player: Player,
    *,
    latest_value: float | None = None,
    total_minutes: float | None = None,
    total_goals: float | None = None,
    total_assists: int | None = None,
    total_cards: int | None = None,
    current_club_name: str | None = None,
) -> dict:
    """Build player response dict (same shape as PlayerResponse)."""
    return {
        "player_id": player.player_id,
        "player_name": player.player_name,
        "date_of_birth": player.date_of_birth,
        "position": player.position,
        "main_position": player.main_position,
        "current_club_id": player.current_club_id,
        "height": player.height,
        "citizenship": player.citizenship,
        "foot": player.foot,
        "player_image_url": player.player_image_url,
        "current_club_name": current_club_name,
        "age": _age_from_dob(player.date_of_birth),
        "market_value": latest_value,
        "minutes_played": total_minutes,
        "total_goals": total_goals,
        "total_assists": total_assists,
        "total_cards": total_cards,
    }


def create_list(db: Session, name: str) -> FavouriteList:
    """Create a favourite list; returns the new model (committed)."""
    obj = FavouriteList(name=name)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_all_lists(db: Session) -> list[FavouriteList]:
    """Return all favourite lists (no pagination)."""
    from sqlalchemy import select

    q = select(FavouriteList).order_by(FavouriteList.id)
    return list(db.execute(q).scalars().unique().all())


def get_list_by_id(db: Session, list_id: int) -> FavouriteList | None:
    """Return one list by id or None."""
    return db.get(FavouriteList, list_id)


def update_list(db: Session, list_id: int, name: str | None) -> FavouriteList | None:
    """Update list name; returns updated model or None if not found."""
    obj = db.get(FavouriteList, list_id)
    if obj is None:
        return None
    if name is not None:
        obj.name = name
    db.commit()
    db.refresh(obj)
    return obj


def delete_list(db: Session, list_id: int) -> bool:
    """Delete list; returns True if deleted, False if not found."""
    obj = db.get(FavouriteList, list_id)
    if obj is None:
        return False
    db.delete(obj)
    db.commit()
    return True


def add_player_to_list(
    db: Session,
    list_id: int,
    player_id: int,
) -> Literal["created", "conflict", "not_found_list", "not_found_player"]:
    """
    Add player to list. Enforces uniqueness (list_id, player_id).
    Returns: created | conflict (already in list) | not_found_list | not_found_player.
    """
    if get_list_by_id(db, list_id) is None:
        return "not_found_list"
    if db.get(Player, player_id) is None:
        return "not_found_player"
    existing = (
        db.execute(
            select(FavouriteListPlayer).where(
                FavouriteListPlayer.list_id == list_id,
                FavouriteListPlayer.player_id == player_id,
            )
        )
        .scalars()
        .first()
    )
    if existing is not None:
        return "conflict"
    db.add(FavouriteListPlayer(list_id=list_id, player_id=player_id))
    db.commit()
    return "created"


def remove_player_from_list(db: Session, list_id: int, player_id: int) -> bool:
    """Remove player from list. Returns True if removed, False if list or link not found."""
    link = (
        db.execute(
            select(FavouriteListPlayer).where(
                FavouriteListPlayer.list_id == list_id,
                FavouriteListPlayer.player_id == player_id,
            )
        )
        .scalars()
        .first()
    )
    if link is None:
        return False
    db.delete(link)
    db.commit()
    return True


def get_players_in_list(
    db: Session,
    list_id: int,
    sort_by: ListSortBy = "name",
    order: ListOrder = "asc",
) -> list[dict]:
    """
    List players in a favourite list with same sort options as player list
    (age, name, market_value, minutes_played). Returns list of player response dicts.
    Does not check if list exists; router should return 404 when list is missing.
    """
    base = (
        select(Player)
        .join(FavouriteListPlayer, Player.player_id == FavouriteListPlayer.player_id)
        .where(FavouriteListPlayer.list_id == list_id)
    )
    if sort_by == "name":
        order_col = Player.player_name
    elif sort_by == "age":
        order_col = Player.date_of_birth
    elif sort_by == "market_value":
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
        base = base.outerjoin(sub_latest, Player.player_id == sub_latest.c.player_id)
        order_col = sub_latest.c.value
    elif sort_by == "minutes_played":
        sub_mins = (
            select(
                PlayerPerformance.player_id,
                func.coalesce(func.sum(PlayerPerformance.minutes_played), 0).label("total_minutes"),
            )
            .group_by(PlayerPerformance.player_id)
            .subquery()
        )
        base = base.outerjoin(sub_mins, Player.player_id == sub_mins.c.player_id)
        order_col = sub_mins.c.total_minutes
    else:
        order_col = Player.player_name
    base = base.order_by(order_col.asc() if order == "asc" else order_col.desc())
    rows = db.execute(base).scalars().unique().all()
    player_ids = [p.player_id for p in rows]
    latest_values: dict[int, float] = {}
    total_minutes_map: dict[int, float] = {}
    total_stats_map: dict[int, dict[str, float | int]] = {}
    current_club_name_map: dict[int, str] = {}
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
        stats_rows = (
            db.execute(
                select(
                    PlayerPerformance.player_id,
                    func.coalesce(func.sum(PlayerPerformance.goals), 0).label("g"),
                    func.coalesce(func.sum(PlayerPerformance.assists), 0).label("a"),
                    func.coalesce(
                        func.sum(
                            func.coalesce(PlayerPerformance.yellow_cards, 0)
                            + func.coalesce(PlayerPerformance.direct_red_cards, 0)
                        ),
                        0,
                    ).label("c"),
                )
                .where(PlayerPerformance.player_id.in_(player_ids))
                .group_by(PlayerPerformance.player_id)
            )
            .all()
        )
        total_stats_map = {
            r.player_id: {"g": float(r.g), "a": int(r.a), "c": int(r.c)} for r in stats_rows
        }
    club_ids = {p.current_club_id for p in rows if p.current_club_id is not None}
    if club_ids:
        club_rows = db.execute(select(Team.club_id, Team.club_name).where(Team.club_id.in_(club_ids))).all()
        current_club_name_map = {r.club_id: r.club_name for r in club_rows}

    result: list[dict] = []
    for p in rows:
        stats = total_stats_map.get(p.player_id) or {}
        result.append(
            _player_to_response_dict(
                p,
                latest_value=latest_values.get(p.player_id),
                total_minutes=total_minutes_map.get(p.player_id),
                total_goals=stats.get("g"),
                total_assists=stats.get("a"),
                total_cards=stats.get("c"),
                current_club_name=current_club_name_map.get(p.current_club_id or 0),
            )
        )
    return result
