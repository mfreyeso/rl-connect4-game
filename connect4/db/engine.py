"""Database engine creation and session management for PostgreSQL and SQLite."""

import os
from collections.abc import Generator
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.engine import Engine

# Default fallback SQLite database file
_DEFAULT_DB_URL = "sqlite:///connect4.db"


def get_db_url() -> str:
    """Return database URL from environment or fallback to SQLite."""
    url = os.environ.get("DATABASE_URL", _DEFAULT_DB_URL)
    # Fix legacy postgres:// schema if provided by hosts like Render/Heroku
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def create_db_engine(db_url: str | None = None) -> Engine:
    """Create SQLModel engine with cross-database adapters (SQLite/PostgreSQL)."""
    target_url = db_url or get_db_url()
    connect_args = {}
    if target_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    return create_engine(target_url, connect_args=connect_args, echo=False)


# Default shared engine
engine = create_db_engine()


def init_db(target_engine: Engine | None = None) -> None:
    """Create all SQLModel tables in target database."""
    db_eng = target_engine or engine
    SQLModel.metadata.create_all(db_eng)


def get_db_session(
    target_engine: Engine | None = None,
) -> Generator[Session, None, None]:
    """Provide a transactional database session."""
    db_eng = target_engine or engine
    with Session(db_eng) as session:
        yield session
