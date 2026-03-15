"""
Player service: list with sort/pagination and get by id.
Sort by age (date_of_birth), name, market_value (latest), minutes_played (sum).
"""

from datetime import date
from typing import Literal

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models import Player, PlayerMarketValue, PlayerPerformance, Team, TransferHistory

# Top 5 European leagues only (for competitions dropdown)
TOP_5_COMPETITION_IDS = ["GB1", "ES1", "IT1", "L1", "FR1"]

# Canonical display names for these competitions (avoid older labels like "Division 1")
COMPETITION_DISPLAY_NAMES: dict[str, str] = {
    "GB1": "Premier League",
    "ES1": "LaLiga",
    "IT1": "Serie A",
    "L1": "Bundesliga",
    "FR1": "Ligue 1",
}

SortBy = Literal[
    "name",
    "age",
    "position",
    "foot",
    "market_value",
    "minutes_played",
    "goals",
    "assists",
    "cards",
    "clean_sheets",
]
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
    total_goals: float | None = None,
    total_assists: int | None = None,
    total_cards: int | None = None,
    total_clean_sheets: int | None = None,
    current_club_name: str | None = None,
    current_club_logo_url: str | None = None,
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
        "foot": player.foot,
        "player_image_url": player.player_image_url,
        "current_club_name": current_club_name,
        "current_club_logo_url": current_club_logo_url,
        "age": _age_from_dob(player.date_of_birth),
        "market_value": latest_value,
        "minutes_played": total_minutes,
        "total_goals": total_goals,
        "total_assists": total_assists,
        "total_cards": total_cards,
        "total_clean_sheets": total_clean_sheets,
    }


def get_players(
    db: Session,
    page: int = 1,
    limit: int = DEFAULT_LIMIT,
    sort_by: SortBy = "market_value",
    order: Order = "desc",
    search: str | None = None,
    competition_id: str | None = None,
    season: str | None = None,
) -> tuple[list[dict], int]:
    """
    List players with pagination and sort.
    If competition_id and/or season are set, only players with at least one performance
    matching that league and season are returned. Stats (minutes, goals, assists, cards)
    and sort-by-minutes are computed only from performances matching the same filters.
    Returns (list of player response dicts, total_count).
    """
    limit = min(max(1, limit), MAX_LIMIT)
    page = max(1, page)
    offset = (page - 1) * limit

    # Performance filter: league and/or season (stats and inclusion use this)
    perf_filters = []
    comp_filter = (competition_id or "").strip()
    season_filter = (season or "").strip()
    if comp_filter:
        perf_filters.append(PlayerPerformance.competition_id == comp_filter)
    if season_filter:
        perf_filters.append(PlayerPerformance.season_name == season_filter)

    if perf_filters:
        sub_players = (
            select(PlayerPerformance.player_id)
            .where(*perf_filters)
            .distinct()
            .subquery()
        )

    # Base query: Player
    q = select(Player)
    if perf_filters:
        q = q.where(Player.player_id.in_(select(sub_players.c.player_id)))

    # Optional name search (case-insensitive, partial)
    search_term = (search or "").strip()
    if search_term:
        q = q.where(Player.player_name.ilike(f"%{search_term}%"))

    if sort_by == "name":
        order_col = Player.player_name
    elif sort_by == "age":
        order_col = Player.date_of_birth
    elif sort_by == "position":
        order_col = Player.position
    elif sort_by == "foot":
        order_col = Player.foot
    elif sort_by == "market_value":
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
        sub_mins = (
            select(
                PlayerPerformance.player_id,
                func.coalesce(func.sum(PlayerPerformance.minutes_played), 0).label("total_minutes"),
            )
            .group_by(PlayerPerformance.player_id)
        )
        if perf_filters:
            sub_mins = sub_mins.where(*perf_filters)
        sub_mins = sub_mins.subquery()
        q = q.outerjoin(sub_mins, Player.player_id == sub_mins.c.player_id)
        order_col = sub_mins.c.total_minutes
    elif sort_by == "goals":
        sub_goals = (
            select(
                PlayerPerformance.player_id,
                func.coalesce(func.sum(PlayerPerformance.goals), 0).label("total_goals"),
            )
            .group_by(PlayerPerformance.player_id)
        )
        if perf_filters:
            sub_goals = sub_goals.where(*perf_filters)
        sub_goals = sub_goals.subquery()
        q = q.outerjoin(sub_goals, Player.player_id == sub_goals.c.player_id)
        order_col = sub_goals.c.total_goals
    elif sort_by == "assists":
        sub_assists = (
            select(
                PlayerPerformance.player_id,
                func.coalesce(func.sum(PlayerPerformance.assists), 0).label("total_assists"),
            )
            .group_by(PlayerPerformance.player_id)
        )
        if perf_filters:
            sub_assists = sub_assists.where(*perf_filters)
        sub_assists = sub_assists.subquery()
        q = q.outerjoin(sub_assists, Player.player_id == sub_assists.c.player_id)
        order_col = sub_assists.c.total_assists
    elif sort_by == "cards":
        sub_cards = (
            select(
                PlayerPerformance.player_id,
                func.coalesce(
                    func.sum(
                        func.coalesce(PlayerPerformance.yellow_cards, 0)
                        + func.coalesce(PlayerPerformance.direct_red_cards, 0)
                    ),
                    0,
                ).label("total_cards"),
            )
            .group_by(PlayerPerformance.player_id)
        )
        if perf_filters:
            sub_cards = sub_cards.where(*perf_filters)
        sub_cards = sub_cards.subquery()
        q = q.outerjoin(sub_cards, Player.player_id == sub_cards.c.player_id)
        order_col = sub_cards.c.total_cards
    elif sort_by == "clean_sheets":
        sub_cs = (
            select(
                PlayerPerformance.player_id,
                func.coalesce(func.sum(PlayerPerformance.clean_sheets), 0).label("total_clean_sheets"),
            )
            .group_by(PlayerPerformance.player_id)
        )
        if perf_filters:
            sub_cs = sub_cs.where(*perf_filters)
        sub_cs = sub_cs.subquery()
        q = q.outerjoin(sub_cs, Player.player_id == sub_cs.c.player_id)
        order_col = sub_cs.c.total_clean_sheets
    else:
        order_col = Player.player_name

    q = q.order_by(order_col.asc() if order == "asc" else order_col.desc())
    count_q = select(func.count()).select_from(Player)
    if perf_filters:
        count_q = count_q.where(Player.player_id.in_(select(sub_players.c.player_id)))
    if search_term:
        count_q = count_q.where(Player.player_name.ilike(f"%{search_term}%"))
    total_count = db.execute(count_q).scalar() or 0

    q = q.offset(offset).limit(limit)
    rows = db.execute(q).scalars().unique().all()

    # Resolve latest value, total minutes, aggregate stats and current club name per player
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
        mins_q = (
            select(
                PlayerPerformance.player_id,
                func.coalesce(func.sum(PlayerPerformance.minutes_played), 0).label("m"),
            )
            .where(PlayerPerformance.player_id.in_(player_ids))
            .group_by(PlayerPerformance.player_id)
        )
        if perf_filters:
            mins_q = mins_q.where(*perf_filters)
        mins_rows = db.execute(mins_q).all()
        total_minutes_map = {r.player_id: float(r.m) for r in mins_rows}

    # goals, assists, cards, clean_sheets (same league+season filter when applied)
    total_stats_map: dict[int, dict[str, float | int]] = {}
    if player_ids:
        stats_q = (
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
                func.coalesce(func.sum(PlayerPerformance.clean_sheets), 0).label("cs"),
            )
            .where(PlayerPerformance.player_id.in_(player_ids))
            .group_by(PlayerPerformance.player_id)
        )
        if perf_filters:
            stats_q = stats_q.where(*perf_filters)
        stats_rows = db.execute(stats_q).all()
        total_stats_map = {
            r.player_id: {"g": float(r.g), "a": int(r.a), "c": int(r.c), "cs": int(r.cs)}
            for r in stats_rows
        }

    # current club name and logo
    current_club_name_map: dict[int, str] = {}
    current_club_logo_url_map: dict[int, str] = {}
    club_ids = {p.current_club_id for p in rows if p.current_club_id is not None}
    if club_ids:
        club_rows = db.execute(
            select(Team.club_id, Team.club_name, Team.logo_url).where(Team.club_id.in_(club_ids))
        ).all()
        for r in club_rows:
            current_club_name_map[r.club_id] = r.club_name
            if r.logo_url:
                current_club_logo_url_map[r.club_id] = r.logo_url

    data = []
    for p in rows:
        stats = total_stats_map.get(p.player_id) or {}
        data.append(
            _player_to_response(
                p,
                latest_value=latest_values.get(p.player_id),
                total_minutes=total_minutes_map.get(p.player_id),
                total_goals=stats.get("g"),
                total_assists=stats.get("a"),
                total_cards=stats.get("c"),
                total_clean_sheets=stats.get("cs"),
                current_club_name=current_club_name_map.get(p.current_club_id or 0),
                current_club_logo_url=current_club_logo_url_map.get(p.current_club_id or 0),
            )
        )
    return data, total_count


def get_player_by_id(db: Session, player_id: int) -> Player | None:
    """Return one Player by id or None."""
    return db.get(Player, player_id)


def get_market_value_history(db: Session, player_id: int) -> list[dict]:
    """Return ordered market value history for a player as list of {date, value}."""
    rows = (
        db.execute(
            select(PlayerMarketValue.date_unix, PlayerMarketValue.value)
            .where(PlayerMarketValue.player_id == player_id)
            .order_by(PlayerMarketValue.date_unix.asc())
        )
        .all()
    )
    return [{"date": r.date_unix, "value": float(r.value)} for r in rows]


def get_current_market_value(db: Session, player_id: int) -> float | None:
    """Return latest market value for a player, or None if no history."""
    sub_max = (
        select(
            func.max(PlayerMarketValue.date_unix).label("max_date"),
        )
        .where(PlayerMarketValue.player_id == player_id)
        .scalar_subquery()
    )
    value = (
        db.execute(
            select(PlayerMarketValue.value).where(
                PlayerMarketValue.player_id == player_id,
                PlayerMarketValue.date_unix == sub_max,
            )
        )
        .scalar()
    )
    return float(value) if value is not None else None


def get_career_summary(db: Session, player_id: int) -> dict:
    """Compute seasons played and previous clubs for a player."""
    # Seasons played: distinct non-empty season_name values
    season_rows = (
        db.execute(
            select(PlayerPerformance.season_name)
            .where(PlayerPerformance.player_id == player_id)
            .where(PlayerPerformance.season_name.isnot(None))
            .where(PlayerPerformance.season_name != "")
            .distinct()
        )
        .all()
    )
    seasons_played = len({r.season_name for r in season_rows if r.season_name})

    # Previous clubs: distinct club_id, club_name, logo_url from performances, excluding current club
    club_rows = (
        db.execute(
            select(Team.club_id, Team.club_name, Team.logo_url)
            .join(  # type: ignore[arg-type]
                PlayerPerformance,
                Team.club_id == PlayerPerformance.team_id,
            )
            .where(PlayerPerformance.player_id == player_id)
            .where(Team.club_name.isnot(None))
            .distinct()
        )
        .all()
    )
    # Dedupe by club_id, keep one row per club
    clubs_by_id: dict[int, tuple[str, str | None]] = {}
    for r in club_rows:
        if r.club_name and r.club_id not in clubs_by_id:
            clubs_by_id[r.club_id] = (r.club_name, r.logo_url)

    current_club_name: str | None = None
    player = get_player_by_id(db, player_id)
    if player and player.current_club_id is not None:
        current_club_name = (
            db.execute(select(Team.club_name).where(Team.club_id == player.current_club_id))
            .scalar()
        )
    if current_club_name:
        for cid, (cname, _) in list(clubs_by_id.items()):
            if cname == current_club_name:
                del clubs_by_id[cid]
                break

    previous_clubs = [
        {"club_name": name, "logo_url": logo_url}
        for _id, (name, logo_url) in sorted(clubs_by_id.items(), key=lambda x: (x[1][0].lower(), x[0]))
    ]

    return {
        "seasons_played": seasons_played,
        "previous_clubs": previous_clubs,
    }


def get_player_details(db: Session, player_id: int) -> dict | None:
    """Return rich player details dict or None if player not found."""
    player = get_player_by_id(db, player_id)
    if player is None:
        return None

    current_value = get_current_market_value(db, player_id)
    history = get_market_value_history(db, player_id)
    career = get_career_summary(db, player_id)

    current_club_name: str | None = None
    current_club_logo_url: str | None = None
    if player.current_club_id is not None:
        club_row = (
            db.execute(
                select(Team.club_name, Team.logo_url).where(Team.club_id == player.current_club_id)
            )
            .first()
        )
        if club_row:
            current_club_name = club_row.club_name
            current_club_logo_url = club_row.logo_url

    return {
        "player_id": player.player_id,
        "player_name": player.player_name,
        "position": player.position,
        "main_position": player.main_position,
        "player_image_url": player.player_image_url,
        "current_club_name": current_club_name,
        "current_club_logo_url": current_club_logo_url,
        "citizenship": player.citizenship,
        "age": _age_from_dob(player.date_of_birth),
        "height": player.height,
        "current_market_value": current_value,
        "market_value_history": history,
        "career": career,
    }


def player_to_response_dict(
    player: Player,
    db: Session | None = None,
) -> dict:
    """Build full response dict for one player (with optional market_value, minutes_played)."""
    latest_value: float | None = None
    total_minutes: float | None = None
    total_goals: float | None = None
    total_assists: int | None = None
    total_cards: int | None = None
    total_clean_sheets: int | None = None
    current_club_name: str | None = None
    current_club_logo_url: str | None = None
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
        stats_row = (
            db.execute(
                select(
                    func.coalesce(func.sum(PlayerPerformance.goals), 0).label("g"),
                    func.coalesce(func.sum(PlayerPerformance.assists), 0).label("a"),
                    func.coalesce(
                        func.sum(
                            func.coalesce(PlayerPerformance.yellow_cards, 0)
                            + func.coalesce(PlayerPerformance.direct_red_cards, 0)
                        ),
                        0,
                    ).label("c"),
                    func.coalesce(func.sum(PlayerPerformance.clean_sheets), 0).label("cs"),
                ).where(PlayerPerformance.player_id == player.player_id)
            )
            .first()
        )
        if stats_row is not None:
            total_goals = float(stats_row.g)
            total_assists = int(stats_row.a)
            total_cards = int(stats_row.c)
            total_clean_sheets = int(stats_row.cs)
        if player.current_club_id is not None:
            club_row = (
                db.execute(
                    select(Team.club_name, Team.logo_url).where(
                        Team.club_id == player.current_club_id
                    )
                )
                .first()
            )
            if club_row:
                current_club_name = club_row.club_name
                current_club_logo_url = club_row.logo_url
    return _player_to_response(
        player,
        latest_value=latest_value,
        total_minutes=total_minutes,
        total_goals=total_goals,
        total_assists=total_assists,
        total_cards=total_cards,
        total_clean_sheets=total_clean_sheets,
        current_club_name=current_club_name,
        current_club_logo_url=current_club_logo_url,
    )


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


def get_competitions(db: Session) -> list[dict]:
    """Return distinct competition_id and canonical competition_name for top-5 leagues.

    Distinctness is by competition_id only (to avoid duplicates when historical
    rows have different competition_name values like "Division 1" vs "Ligue 1").
    """
    q = (
        select(PlayerPerformance.competition_id)
        .where(PlayerPerformance.competition_id.in_(TOP_5_COMPETITION_IDS))
        .distinct()
        .order_by(PlayerPerformance.competition_id.asc())
    )
    rows = db.execute(q).all()
    return [
        {
            "competition_id": r.competition_id,
            "competition_name": COMPETITION_DISPLAY_NAMES.get(r.competition_id, r.competition_id),
        }
        for r in rows
    ]


def get_seasons(db: Session) -> list[dict]:
    """Return a small, ordered list of recent seasons for dropdowns.

    We normalise and sort in Python so that strings like \"25/26\", \"24/25\", \"23/24\",
    \"22/23\" appear in the expected newest-first order, independent of lexicographic
    ordering in the database. Limited to the latest 4 seasons.
    """

    q = (
        select(PlayerPerformance.season_name)
        .where(PlayerPerformance.season_name.isnot(None))
        .where(PlayerPerformance.season_name != "")
        .distinct()
    )
    rows = db.execute(q).all()
    raw_seasons = [r.season_name for r in rows if r.season_name]

    def _season_sort_key(s: str) -> int:
        """Map season strings like '25/26' or '2023' to an integer for sorting.

        Higher = more recent. Falls back to 0 if parsing fails.
        """
        s = s.strip()
        if not s:
            return 0
        # Patterns like '25/26' or '2024/25'
        if "/" in s:
            left, *_ = s.split("/", 1)
            try:
                n = int(left)
            except ValueError:
                return 0
            # Heuristic: '25' -> 2025, '99' -> 1999
            if 0 <= n <= 39:  # treat 00–39 as 2000–2039
                return 2000 + n
            if 40 <= n <= 99:  # older seasons like 98/99
                return 1900 + n
            return n
        # Plain year like '2023'
        try:
            return int(s)
        except ValueError:
            return 0

    unique_sorted = sorted(set(raw_seasons), key=_season_sort_key, reverse=True)
    top_four = unique_sorted[:4]
    return [{"season_name": s} for s in top_four]
