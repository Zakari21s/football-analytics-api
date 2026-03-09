#!/usr/bin/env python3
"""
Step 0: Filter the dataset to top-5 European leagues only.

- Builds allowed_club_ids from team_details and team_competitions_seasons
  (competition_id in TOP_5_COMPETITION_IDS).
- Builds allowed_player_ids from player_performances (competition_id in TOP_5)
  union player_profiles (current_club_id in allowed_club_ids).
- Writes filtered CSVs to web/filtered/ (option A). Row counts are printed for verification.

Usage: run from project root: python scripts/filter_dataset.py

The import script can later use these filtered CSVs, or use the same logic and filter on read (option B).
"""

import csv
import json
import sys
from pathlib import Path

# Project root (parent of scripts/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = PROJECT_ROOT / "web" / "archive"
FILTERED = PROJECT_ROOT / "web" / "filtered"

from constants import TOP_5_COMPETITION_IDS


def _build_allowed_club_ids() -> set[int]:
    """Build set of club_id where competition_id is in top-5 leagues."""
    allowed: set[int] = set()
    top5 = set(TOP_5_COMPETITION_IDS)

    # team_details: has competition_id
    path = ARCHIVE / "team_details" / "team_details.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}")
    with path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            cid = (row.get("competition_id") or "").strip()
            if cid in top5:
                try:
                    allowed.add(int(row["club_id"]))
                except (ValueError, KeyError):
                    pass

    # team_competitions_seasons: has competition_id
    path = ARCHIVE / "team_competitions_seasons" / "team_competitions_seasons.csv"
    if path.exists():
        with path.open(newline="", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                cid = (row.get("competition_id") or "").strip()
                if cid in top5:
                    try:
                        allowed.add(int(row["club_id"]))
                    except (ValueError, KeyError):
                        pass

    return allowed


def _build_allowed_player_ids(allowed_club_ids: set[int]) -> set[int]:
    """Build set of player_id: from performances (competition in TOP_5) union profiles (current_club in allowed)."""
    allowed: set[int] = set()
    top5 = set(TOP_5_COMPETITION_IDS)

    # From player_performances where competition_id in TOP_5
    path = ARCHIVE / "player_performances" / "player_performances.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}")
    with path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            cid = (row.get("competition_id") or "").strip()
            if cid in top5:
                try:
                    allowed.add(int(row["player_id"]))
                except (ValueError, KeyError):
                    pass

    # Optionally union: players whose current_club_id is in allowed_club_ids
    path = ARCHIVE / "player_profiles" / "player_profiles.csv"
    if path.exists():
        with path.open(newline="", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                try:
                    club_id = row.get("current_club_id")
                    if club_id is None or club_id == "":
                        continue
                    if int(club_id) in allowed_club_ids:
                        allowed.add(int(row["player_id"]))
                except (ValueError, KeyError):
                    pass

    return allowed


def _write_filtered_csv(
    subdir: str,
    filename: str,
    filter_fn,
    required_columns: list[str] | None = None,
) -> int:
    """
    Read CSV from archive, keep rows where filter_fn(row) is True, write to filtered/.
    Returns number of rows written.
    """
    src = ARCHIVE / subdir / filename
    dst_dir = FILTERED / subdir
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / filename

    if not src.exists():
        print(f"  Skip (missing): {src}")
        return 0

    count = 0
    with src.open(newline="", encoding="utf-8") as fin:
        reader = csv.DictReader(fin)
        fieldnames = reader.fieldnames
        if not fieldnames:
            return 0
        with dst.open("w", newline="", encoding="utf-8") as fout:
            writer = csv.DictWriter(fout, fieldnames=fieldnames)
            writer.writeheader()
            for row in reader:
                if filter_fn(row):
                    writer.writerow(row)
                    count += 1
    return count


def run_filter() -> dict[str, int]:
    """Build sets, write filtered CSVs, return row counts per file."""
    print("Building allowed_club_ids...")
    allowed_club_ids = _build_allowed_club_ids()
    print(f"  allowed_club_ids: {len(allowed_club_ids)}")

    print("Building allowed_player_ids...")
    allowed_player_ids = _build_allowed_player_ids(allowed_club_ids)
    print(f"  allowed_player_ids: {len(allowed_player_ids)}")

    top5 = set(TOP_5_COMPETITION_IDS)
    counts: dict[str, int] = {}

    FILTERED.mkdir(parents=True, exist_ok=True)

    # team_details: competition_id in TOP_5
    def team_details_ok(row):
        return (row.get("competition_id") or "").strip() in top5

    c = _write_filtered_csv("team_details", "team_details.csv", team_details_ok)
    counts["team_details"] = c
    print(f"  team_details: {c} rows")

    # team_competitions_seasons: competition_id in TOP_5
    def tcs_ok(row):
        return (row.get("competition_id") or "").strip() in top5

    c = _write_filtered_csv("team_competitions_seasons", "team_competitions_seasons.csv", tcs_ok)
    counts["team_competitions_seasons"] = c
    print(f"  team_competitions_seasons: {c} rows")

    # player_performances: competition_id in TOP_5
    def perf_ok(row):
        return (row.get("competition_id") or "").strip() in top5

    c = _write_filtered_csv("player_performances", "player_performances.csv", perf_ok)
    counts["player_performances"] = c
    print(f"  player_performances: {c} rows")

    # player_profiles: player_id in allowed_player_ids
    def profile_ok(row):
        try:
            return int(row["player_id"]) in allowed_player_ids
        except (ValueError, KeyError):
            return False

    c = _write_filtered_csv("player_profiles", "player_profiles.csv", profile_ok)
    counts["player_profiles"] = c
    print(f"  player_profiles: {c} rows")

    # transfer_history: from_team_id and to_team_id in allowed_club_ids (or player in allowed)
    def transfer_ok(row):
        try:
            pid = int(row["player_id"])
            from_id = int(row.get("from_team_id") or 0)
            to_id = int(row.get("to_team_id") or 0)
            if pid in allowed_player_ids:
                return True
            if from_id in allowed_club_ids or to_id in allowed_club_ids:
                return True
            return False
        except (ValueError, KeyError):
            return False

    c = _write_filtered_csv("transfer_history", "transfer_history.csv", transfer_ok)
    counts["transfer_history"] = c
    print(f"  transfer_history: {c} rows")

    # player_market_value: player_id in allowed_player_ids
    def mv_ok(row):
        try:
            return int(row["player_id"]) in allowed_player_ids
        except (ValueError, KeyError):
            return False

    c = _write_filtered_csv("player_market_value", "player_market_value.csv", mv_ok)
    counts["player_market_value"] = c
    print(f"  player_market_value: {c} rows")

    # player_latest_market_value: player_id in allowed_player_ids
    c = _write_filtered_csv("player_latest_market_value", "player_latest_market_value.csv", mv_ok)
    counts["player_latest_market_value"] = c
    print(f"  player_latest_market_value: {c} rows")

    # Save sets for import script (option B: filter-at-import)
    sets_path = FILTERED / "allowed_ids.json"
    with sets_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "allowed_club_ids": sorted(allowed_club_ids),
                "allowed_player_ids": sorted(allowed_player_ids),
            },
            f,
            indent=0,
        )
    print(f"  Saved {sets_path} (for import script if using filter-on-read)")

    return counts


def main() -> int:
    print("Step 0: Filter dataset to top-5 leagues:", TOP_5_COMPETITION_IDS)
    print("Output: web/filtered/\n")
    try:
        counts = run_filter()
        print("\nDone. Row counts:")
        for name, n in counts.items():
            print(f"  {name}: {n}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
