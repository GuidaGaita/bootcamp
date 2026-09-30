"""Weak Argon2id parameters must prevent startup outside tests (FR-020, docs/04 §5)."""

import os

import pytest
from fastapi.testclient import TestClient

from cofre.core.config import ConfigurationError
from cofre.main import create_app
from tests.conftest import sqlite_url

pytestmark = [pytest.mark.security, pytest.mark.req("RNF-02")]


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch, tmp_path):
    for name in list(os.environ):
        if name.startswith("COFRE_"):
            monkeypatch.delenv(name)
    monkeypatch.setenv("COFRE_DATABASE_URL", sqlite_url(tmp_path / "cofre.db"))


@pytest.mark.parametrize("env", ["production", "development"])
@pytest.mark.parametrize(
    ("variable", "weak_value"),
    [
        ("COFRE_ARGON2_MEMORY_KIB", "19455"),
        ("COFRE_ARGON2_TIME_COST", "1"),
        ("COFRE_ARGON2_PARALLELISM", "0"),
    ],
)
def test_weak_argon2_parameter_prevents_startup(monkeypatch, env, variable, weak_value):
    monkeypatch.setenv("COFRE_ENV", env)
    monkeypatch.setenv(variable, weak_value)

    with pytest.raises(ConfigurationError, match=variable):
        create_app()


@pytest.mark.parametrize("env", ["production", "development"])
def test_exact_minimums_start(monkeypatch, env):
    monkeypatch.setenv("COFRE_ENV", env)
    monkeypatch.setenv("COFRE_ARGON2_MEMORY_KIB", "19456")
    monkeypatch.setenv("COFRE_ARGON2_TIME_COST", "2")
    monkeypatch.setenv("COFRE_ARGON2_PARALLELISM", "1")

    with TestClient(create_app()) as client:
        assert client.get("/health").status_code == 200


def test_reduced_parameters_are_allowed_in_test_environment(monkeypatch):
    monkeypatch.setenv("COFRE_ENV", "test")
    monkeypatch.setenv("COFRE_ARGON2_MEMORY_KIB", "1024")

    with TestClient(create_app()) as client:
        assert client.get("/health").status_code == 200
