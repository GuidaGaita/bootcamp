import pytest
from fastapi.testclient import TestClient

from cofre.core.config import Settings
from cofre.main import create_app
from tests.support import probe
from tests.support.clock import FakeClock


def sqlite_url(path) -> str:
    return f"sqlite:///{path.as_posix()}"


def make_settings(tmp_path, **overrides) -> Settings:
    values = {
        "env": "test",
        "database_url": sqlite_url(tmp_path / "cofre.db"),
        "argon2_memory_kib": 1024,
        "argon2_time_cost": 1,
        "argon2_parallelism": 1,
    }
    values.update(overrides)
    return Settings(**values)


@pytest.fixture
def settings(tmp_path) -> Settings:
    return make_settings(tmp_path)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def app(settings, clock):
    application = create_app(settings, clock)
    application.include_router(probe.router)
    return application


@pytest.fixture
def client(app):
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
