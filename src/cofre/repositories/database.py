"""SQLite persistence plumbing (research R6, R7)."""

from pathlib import Path

from sqlalchemy import Engine, create_engine, make_url, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Declarative base; tables arrive with units 002 and 003."""


def build_engine(url: str) -> Engine:
    return create_engine(url, connect_args={"check_same_thread": False})


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def ping(engine: Engine) -> None:
    """Run ``SELECT 1`` on a fresh connection; raises if the database is unreachable."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def init_schema(engine: Engine, url: str) -> None:
    """Create the SQLite file's parent directory, if missing, and all known tables."""
    database = make_url(url).database
    if database and database != ":memory:":
        Path(database).parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)
