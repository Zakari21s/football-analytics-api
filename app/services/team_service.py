"""
Team service: list with pagination and get by id.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Team

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


def get_teams(
    db: Session,
    page: int = 1,
    limit: int = DEFAULT_LIMIT,
) -> tuple[list[Team], int]:
    """
    List teams with pagination. Returns (list of Team, total_count).
    """
    limit = min(max(1, limit), MAX_LIMIT)
    page = max(1, page)
    offset = (page - 1) * limit

    total_count = db.execute(select(func.count()).select_from(Team)).scalar() or 0
    q = select(Team).order_by(Team.club_id).offset(offset).limit(limit)
    rows = db.execute(q).scalars().unique().all()
    return list(rows), total_count


def get_team_by_id(db: Session, team_id: int) -> Team | None:
    """Return one Team by club_id or None."""
    return db.get(Team, team_id)
