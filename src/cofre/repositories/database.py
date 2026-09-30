"""SQLite persistence plumbing (research R6, R7)."""

from pathlib import Path

from sqlalchemy import Engine, create_engine, make_url, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool, StaticPool


class Base(DeclarativeBase):
    """Declarative base; tables arrive with units 002 and 003."""


def _is_in_memory(url: str) -> bool:
    return make_url(url).database in (None, "", ":memory:")


def build_engine(url: str) -> Engine:
    """File databases open a new connection per checkout, so ``ping`` never reuses one;
    an in-memory database keeps a single connection shared by every thread."""
    pool = StaticPool if _is_in_memory(url) else NullPool
    return create_engine(url, connect_args={"check_same_thread": False}, poolclass=pool)


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def ping(engine: Engine) -> None:
    """Read the schema page on a fresh connection; raises if the database is unusable.

    ``SELECT 1`` alone never touches the file, so a corrupted database would pass.
    """
    with engine.connect() as connection:
        connection.execute(text("SELECT count(*) FROM sqlite_master"))


def init_schema(engine: Engine, url: str) -> None:
    """Create the SQLite file's parent directory, if missing, and all known tables."""
    if not _is_in_memory(url):
        Path(make_url(url).database).parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)
