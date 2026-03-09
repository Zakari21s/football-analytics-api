#!/usr/bin/env python3
"""
Step 3: Load filtered dataset from web/filtered/ into the database.

Import order (respect FKs): (1) Teams, (2) Players, (3) PlayerPerformances,
(4) TransferHistory, (5) PlayerMarketValue. Uses batch commits and streams
CSVs to avoid loading everything into memory.

Run from project root: python scripts/load_data.py

Expects: web/filtered/ with team_details, player_profiles, player_performances,
transfer_history, player_market_value. Run scripts/filter_dataset.py first if needed.
"""

import csv
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import (
    Player,
    PlayerMarketValue,
    PlayerPerformance,
    Team,
    TransferHistory,
)

# Import app.models registers all models with Base
FILTERED = PROJECT_ROOT / "web" / "filtered"
BATCH_SIZE = 5000


def _parse_date(s: str | None):
    if not s or not str(s).strip():
        return None
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%Y"):
        try:
            return datetime.strptime(s[:10], fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def _safe_int(v, default=None):
    if v is None or v == "":
        return default
    try:
        return int(float(str(v).replace(",", "")))
    except (ValueError, TypeError):
        return default


def _safe_float(v, default=None):
    if v is None or v == "":
        return default
    try:
        return float(str(v).replace(",", ""))
    except (ValueError, TypeError):
        return default


def _str_trim(s, max_len=255):
    if s is None:
        return None
    t = str(s).strip()
    return t[:max_len] if t else None


def load_teams(session: Session) -> set[int]:
    """Load teams from web/filtered/team_details; deduplicate by club_id. Returns set of club_ids."""
    path = FILTERED / "team_details" / "team_details.csv"
    if not path.exists():
        print(f"  Skip teams (missing {path})")
        return set()
    seen: set[int] = set()
    count = 0
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = _safe_int(row.get("club_id"))
            if cid is None or cid in seen:
                continue
            seen.add(cid)
            session.add(
                Team(
                    club_id=cid,
                    club_name=_str_trim(row.get("club_name")) or f"Club {cid}",
                    country_name=_str_trim(row.get("country_name"), 128),
                    competition_id=_str_trim(row.get("competition_id"), 32),
                    competition_name=_str_trim(row.get("competition_name"), 128),
                    season_id=_str_trim(row.get("season_id"), 32),
                )
            )
            count += 1
    session.commit()
    print(f"  teams: {count}")
    return seen


def load_players(session: Session, valid_club_ids: set[int]) -> set[int]:
    """Load players from web/filtered/player_profiles. current_club_id set only if in valid_club_ids. Returns set of inserted player_ids."""
    path = FILTERED / "player_profiles" / "player_profiles.csv"
    if not path.exists():
        print(f"  Skip players (missing {path})")
        return set()
    count = 0
    inserted_ids: set[int] = set()
    batch: list[Player] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = _safe_int(row.get("player_id"))
            if pid is None:
                continue
            current_club_id = _safe_int(row.get("current_club_id"))
            if current_club_id is not None and current_club_id not in valid_club_ids:
                current_club_id = None
            try:
                batch.append(
                    Player(
                        player_id=pid,
                        player_slug=_str_trim(row.get("player_slug"), 255),
                        player_name=_str_trim(row.get("player_name")) or f"Player {pid}",
                        date_of_birth=_parse_date(row.get("date_of_birth")),
                        position=_str_trim(row.get("position"), 128),
                        main_position=_str_trim(row.get("main_position"), 64),
                        current_club_id=current_club_id,
                        height=_safe_float(row.get("height")),
                        citizenship=_str_trim(row.get("citizenship"), 128),
                    )
                )
                inserted_ids.add(pid)
            except Exception:
                continue
            count += 1
            if len(batch) >= BATCH_SIZE:
                session.bulk_save_objects(batch)
                session.commit()
                batch = []
        if batch:
            session.bulk_save_objects(batch)
            session.commit()
    print(f"  players: {count}")
    return inserted_ids


def load_player_performances(session: Session, valid_player_ids: set[int]) -> int:
    """Load from web/filtered/player_performances. Only rows with player_id in valid_player_ids."""
    path = FILTERED / "player_performances" / "player_performances.csv"
    if not path.exists():
        print(f"  Skip player_performances (missing {path})")
        return 0
    count = 0
    batch: list[PlayerPerformance] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = _safe_int(row.get("player_id"))
            if pid is None or pid not in valid_player_ids:
                continue
            try:
                batch.append(
                    PlayerPerformance(
                        player_id=pid,
                        season_name=_str_trim(row.get("season_name"), 32),
                        competition_id=_str_trim(row.get("competition_id"), 32),
                        competition_name=_str_trim(row.get("competition_name"), 128),
                        team_id=_safe_int(row.get("team_id")),
                        goals=_safe_float(row.get("goals")),
                        assists=_safe_int(row.get("assists")),
                        minutes_played=_safe_float(row.get("minutes_played")),
                        yellow_cards=_safe_int(row.get("yellow_cards")),
                        direct_red_cards=_safe_int(row.get("direct_red_cards")),
                        clean_sheets=_safe_int(row.get("clean_sheets")),
                    )
                )
            except Exception:
                continue
            count += 1
            if len(batch) >= BATCH_SIZE:
                session.bulk_save_objects(batch)
                session.commit()
                batch = []
        if batch:
            session.bulk_save_objects(batch)
            session.commit()
    print(f"  player_performances: {count}")
    return count


def load_transfer_history(session: Session, valid_player_ids: set[int]) -> int:
    """Load from web/filtered/transfer_history. Only rows with player_id in valid_player_ids."""
    path = FILTERED / "transfer_history" / "transfer_history.csv"
    if not path.exists():
        print(f"  Skip transfer_history (missing {path})")
        return 0
    count = 0
    batch: list[TransferHistory] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = _safe_int(row.get("player_id"))
            if pid is None or pid not in valid_player_ids:
                continue
            try:
                batch.append(
                    TransferHistory(
                        player_id=pid,
                        season_name=_str_trim(row.get("season_name"), 32),
                        transfer_date=_parse_date(row.get("transfer_date")),
                        from_team_id=_safe_int(row.get("from_team_id")),
                        to_team_id=_safe_int(row.get("to_team_id")),
                        transfer_type=_str_trim(row.get("transfer_type"), 64),
                        value_at_transfer=_safe_float(row.get("value_at_transfer")),
                        transfer_fee=_safe_float(row.get("transfer_fee")),
                    )
                )
            except Exception:
                continue
            count += 1
            if len(batch) >= BATCH_SIZE:
                session.bulk_save_objects(batch)
                session.commit()
                batch = []
        if batch:
            session.bulk_save_objects(batch)
            session.commit()
    print(f"  transfer_history: {count}")
    return count


def load_player_market_value(session: Session, valid_player_ids: set[int]) -> int:
    """Load from web/filtered/player_market_value. Only rows with player_id in valid_player_ids. date_unix in CSV is date string."""
    path = FILTERED / "player_market_value" / "player_market_value.csv"
    if not path.exists():
        print(f"  Skip player_market_value (missing {path})")
        return 0
    count = 0
    batch: list[PlayerMarketValue] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = _safe_int(row.get("player_id"))
            if pid is None or pid not in valid_player_ids:
                continue
            dt = _parse_date(row.get("date_unix"))
            if dt is None:
                continue
            val = _safe_float(row.get("value"), 0.0)
            if val is None:
                val = 0.0
            try:
                batch.append(
                    PlayerMarketValue(
                        player_id=pid,
                        date_unix=dt,
                        value=val,
                    )
                )
            except Exception:
                continue
            count += 1
            if len(batch) >= BATCH_SIZE:
                session.bulk_save_objects(batch)
                session.commit()
                batch = []
        if batch:
            session.bulk_save_objects(batch)
            session.commit()
    print(f"  player_market_value: {count}")
    return count


def main() -> int:
    if not FILTERED.is_dir():
        print(f"Error: web/filtered/ not found at {FILTERED}. Run scripts/filter_dataset.py first.")
        return 1
    print("Loading data from web/filtered/ into DB...")
    session = SessionLocal()
    try:
        valid_club_ids = load_teams(session)
        valid_player_ids = load_players(session, valid_club_ids)
        load_player_performances(session, valid_player_ids)
        load_transfer_history(session, valid_player_ids)
        load_player_market_value(session, valid_player_ids)
        print("Done.")
        return 0
    except Exception as e:
        session.rollback()
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
