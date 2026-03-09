#!/usr/bin/env python3
"""
Legacy/stub: dataset import is implemented in scripts/load_data.py.

Use: python scripts/load_data.py
Reads from web/filtered/ and imports in FK order: teams → players → player_performances
→ transfer_history → player_market_value. Run scripts/filter_dataset.py first to produce web/filtered/.
"""

from constants import TOP_5_COMPETITION_IDS

if __name__ == "__main__":
    print("Use scripts/load_data.py to import from web/filtered/ into the DB.")
    print("TOP_5_COMPETITION_IDS:", TOP_5_COMPETITION_IDS)
