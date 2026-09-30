import pytest
from fastapi.testclient import TestClient

from cofre.core.config import Settings
from cofre.main import create_app
from tests.support import probe
from tests.support.clock import FakeClock

pytest_plugins = ["pytester", "tests.harness.plugin"]


def sqlite_url(path) -> str:
    return f"sqlite:///{path.as_posix()}"


class IsolatedSettings(Settings):
    """Settings built only from explicit values: COFRE_* from the shell never leak in."""

    @classmethod
    def settings_customise_sources(cls, settings_cls, init_settings, **_sources):
        return (init_settings,)


def make_settings(tmp_path, **overrides) -> Settings:
    values = {
        "env": "test",
        "database_url": sqlite_url(tmp_path / "cofre.db"),
        "argon2_memory_kib": 1024,
        "argon2_time_cost": 1,
        "argon2_parallelism": 1,
    }
    values.update(overrides)
    return IsolatedSettings(**values)


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
