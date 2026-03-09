"""
Database engine, session factory, and dependency for FastAPI.
Use get_db() in route dependencies; services receive the yielded session.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import DATABASE_URL

# SQLite: enable foreign keys and use check_same_thread=False for FastAPI
connect_args: dict = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,  # Set True for SQL logging in dev
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency that yields a DB session; commit/rollback handled by caller or middleware."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
