#!/usr/bin/env python3
"""
Populate teams.logo_url from web/filtered/team_details/team_details.csv.
Run after add_teams_logo_url_column.py if the DB already had teams without logos.

Run from project root: python scripts/update_teams_logo_url.py
"""

import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

FILTERED = PROJECT_ROOT / "web" / "filtered"
TEAM_DETAILS_CSV = FILTERED / "team_details" / "team_details.csv"


def _str_trim(s, max_len=512):
    if s is None:
        return None
    t = str(s).strip()
    return t[:max_len] if t else None


def main() -> None:
    if not TEAM_DETAILS_CSV.exists():
        print(f"Missing {TEAM_DETAILS_CSV}")
        sys.exit(1)

    # Build club_id -> logo_url (first occurrence per club)
    logo_by_club: dict[int, str] = {}
    with TEAM_DETAILS_CSV.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid_str = row.get("club_id")
            if not cid_str:
                continue
            try:
                cid = int(cid_str)
            except (ValueError, TypeError):
                continue
            if cid in logo_by_club:
                continue
            url = _str_trim(row.get("logo_url"), 512)
            if url:
                logo_by_club[cid] = url

    if not logo_by_club:
        print("No logo_url values found in CSV.")
        sys.exit(0)

    from sqlalchemy import text
    from app.database import engine

    updated = 0
    with engine.connect() as conn:
        for club_id, logo_url in logo_by_club.items():
            r = conn.execute(
                text("UPDATE teams SET logo_url = :url WHERE club_id = :cid"),
                {"url": logo_url, "cid": club_id},
            )
            if r.rowcount:
                updated += r.rowcount
        conn.commit()

    print(f"Updated logo_url for {updated} team(s).")
    sys.exit(0)


if __name__ == "__main__":
    main()
