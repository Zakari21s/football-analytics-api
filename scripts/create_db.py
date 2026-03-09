#!/usr/bin/env python3
"""
Create database tables from SQLAlchemy models (create_all).
Run from project root: python scripts/create_db.py

Uses DATABASE_URL from environment (or .env). No data is loaded; use filter_and_import.py for that.
"""

import sys
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.database import Base, engine

# Import models so they are registered with Base
from app import models  # noqa: F401

if __name__ == "__main__":
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    tables = list(Base.metadata.tables.keys())
    print(f"Created {len(tables)} tables: {', '.join(sorted(tables))}")
