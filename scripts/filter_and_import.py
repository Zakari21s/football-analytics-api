#!/usr/bin/env python3
"""
Import filtered data into the database (after Step 0: filter_dataset.py).

- Step 0 is in scripts/filter_dataset.py: it builds allowed_club_ids and allowed_player_ids,
  and writes filtered CSVs to web/filtered/ (option A). Run: python scripts/filter_dataset.py
- This script will read from web/filtered/ and import in FK order:
  teams → players → player_performances, transfer_history, player_market_value.
See project plan section 3.1 for column mapping and filter order.
"""

from constants import TOP_5_COMPETITION_IDS

# Implementation: read web/filtered/*.csv (or web/archive + allowed_ids.json for option B), import in FK order.
# Stub – to be implemented.

if __name__ == "__main__":
    print("filter_and_import.py – stub. Implement DB import from web/filtered/.")
    print("TOP_5_COMPETITION_IDS:", TOP_5_COMPETITION_IDS)
