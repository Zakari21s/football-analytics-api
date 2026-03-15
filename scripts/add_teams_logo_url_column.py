#!/usr/bin/env python3
"""
Add teams.logo_url column if missing (migration for existing databases).
Run from project root: python scripts/add_teams_logo_url_column.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text

from app.database import engine


def main() -> None:
    with engine.connect() as conn:
        # Check if logo_url already exists on teams
        result = conn.execute(text("PRAGMA table_info(teams)"))
        columns = [row[1] for row in result.fetchall()]
        if "logo_url" in columns:
            print("Column teams.logo_url already exists. Nothing to do.")
            return
        conn.execute(text("ALTER TABLE teams ADD COLUMN logo_url VARCHAR(512)"))
        conn.commit()
        print("Added column teams.logo_url.")
    print("Done. Re-run scripts/load_data.py to populate logo_url from team_details.csv.")


if __name__ == "__main__":
    main()
    sys.exit(0)
