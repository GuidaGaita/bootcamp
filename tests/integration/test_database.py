from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import text

from cofre.repositories.database import (
    build_engine,
    build_session_factory,
    init_schema,
    ping,
)

pytestmark = [pytest.mark.integration, pytest.mark.req("RF-01")]


def _url(path) -> str:
    return f"sqlite:///{path.as_posix()}"


def test_ping_succeeds_with_sqlite_file(tmp_path):
    engine = build_engine(_url(tmp_path / "cofre.db"))
    try:
        ping(engine)
    finally:
        engine.dispose()


def test_ping_raises_when_url_points_to_directory(tmp_path):
    engine = build_engine(_url(tmp_path))
    try:
        with pytest.raises(Exception):  # noqa: B017
            ping(engine)
    finally:
        engine.dispose()


def test_init_schema_creates_missing_parent_directory(tmp_path):
    url = _url(tmp_path / "nested" / "dir" / "cofre.db")
    engine = build_engine(url)
    try:
        init_schema(engine, url)
        assert (tmp_path / "nested" / "dir").is_dir()
        ping(engine)
    finally:
        engine.dispose()


def test_init_schema_ignores_in_memory_database():
    url = "sqlite://"
    engine = build_engine(url)
    try:
        init_schema(engine, url)
        ping(engine)
    finally:
        engine.dispose()


def test_session_factory_opens_working_session(tmp_path):
    engine = build_engine(_url(tmp_path / "cofre.db"))
    factory = build_session_factory(engine)
    try:
        with factory() as session:
            assert session.execute(text("SELECT 1")).scalar_one() == 1
        assert not session.in_transaction()
    finally:
        engine.dispose()


def test_ping_detects_database_corrupted_after_successful_ping(tmp_path):
    path = tmp_path / "cofre.db"
    engine = build_engine(_url(path))
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE t (id INTEGER)"))
        ping(engine)

        path.write_bytes(b"not a sqlite database" * 100)

        with pytest.raises(Exception):  # noqa: B017
            ping(engine)
    finally:
        engine.dispose()


def test_in_memory_database_is_shared_across_threads():
    engine = build_engine("sqlite://")
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE t (id INTEGER)"))

        def count_tables() -> int:
            with engine.connect() as connection:
                return connection.execute(
                    text("SELECT count(*) FROM sqlite_master WHERE name = 't'")
                ).scalar_one()

        with ThreadPoolExecutor(max_workers=1) as executor:
            assert executor.submit(count_tables).result() == 1
    finally:
        engine.dispose()
