import importlib
import os

import pytest
from fastapi.testclient import TestClient

import cofre.main
from cofre.core.clock import SystemClock
from cofre.main import create_app
from tests.conftest import make_settings
from tests.support.clock import FakeClock

pytestmark = [pytest.mark.api, pytest.mark.req("RNF-09", "RNF-10")]


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    for name in list(os.environ):
        if name.startswith("COFRE_"):
            monkeypatch.delenv(name)


def test_factory_without_arguments_reads_environment_and_uses_system_clock(monkeypatch, tmp_path):
    monkeypatch.setenv("COFRE_ENV", "test")
    monkeypatch.setenv("COFRE_DATABASE_URL", f"sqlite:///{(tmp_path / 'env.db').as_posix()}")

    app = create_app()

    assert app.state.settings.env == "test"
    assert isinstance(app.state.clock, SystemClock)


def test_importing_module_does_not_read_environment(monkeypatch):
    monkeypatch.setenv("COFRE_ENV", "staging")

    importlib.reload(cofre.main)


def test_applications_do_not_share_database_or_clock(tmp_path):
    first_dir, second_dir = tmp_path / "a", tmp_path / "b"
    first_clock, second_clock = FakeClock(), FakeClock()
    first = create_app(make_settings(first_dir), first_clock)
    second = create_app(make_settings(second_dir), second_clock)

    with TestClient(first) as client_a, TestClient(second) as client_b:
        assert client_a.get("/health").status_code == 200
        assert client_b.get("/health").status_code == 200
        first_clock.advance(hours=1)

        assert first.state.clock.now() != second.state.clock.now()
        assert first.state.engine is not second.state.engine

    assert (first_dir / "cofre.db").is_file()
    assert (second_dir / "cofre.db").is_file()


@pytest.mark.req("RNF-15")
def test_default_database_is_created_relative_to_working_directory(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    with TestClient(create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert (tmp_path / "data" / "cofre.db").is_file()
