import os

import pytest

from cofre.core.config import ConfigurationError, Settings, load_settings

pytestmark = [pytest.mark.unit, pytest.mark.req("RNF-10")]

DEFAULTS = {
    "env": "production",
    "database_url": "sqlite:///./data/cofre.db",
    "session_ttl_minutes": 30,
    "login_max_attempts": 5,
    "login_lock_minutes": 15,
    "max_credentials_per_user": 1000,
    "argon2_memory_kib": 19456,
    "argon2_time_cost": 2,
    "argon2_parallelism": 1,
    "log_level": "INFO",
}

POSITIVE_INTEGERS = [
    "COFRE_SESSION_TTL_MINUTES",
    "COFRE_LOGIN_MAX_ATTEMPTS",
    "COFRE_LOGIN_LOCK_MINUTES",
    "COFRE_MAX_CREDENTIALS_PER_USER",
]


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    for name in list(os.environ):
        if name.startswith("COFRE_"):
            monkeypatch.delenv(name)


def test_defaults_match_data_model():
    assert load_settings().model_dump() == DEFAULTS


def test_settings_are_immutable():
    settings = load_settings()

    with pytest.raises(Exception):  # noqa: B017 - pydantic raises ValidationError
        settings.env = "test"


def test_log_level_is_case_insensitive(monkeypatch):
    monkeypatch.setenv("COFRE_LOG_LEVEL", "debug")

    assert load_settings().log_level == "DEBUG"


def test_reads_values_from_environment(monkeypatch):
    monkeypatch.setenv("COFRE_ENV", "development")
    monkeypatch.setenv("COFRE_SESSION_TTL_MINUTES", "45")

    settings = load_settings()

    assert settings.env == "development"
    assert settings.session_ttl_minutes == 45


@pytest.mark.req("RNF-04")
@pytest.mark.parametrize(
    ("variable", "value"),
    [
        ("COFRE_ENV", "staging"),
        ("COFRE_LOG_LEVEL", "verbose"),
        ("COFRE_DATABASE_URL", "postgresql://MARCADOR-URL/db"),
        *[(name, value) for name in POSITIVE_INTEGERS for value in ("0", "-1")],
        ("COFRE_SESSION_TTL_MINUTES", "trinta"),
    ],
)
def test_invalid_value_raises_configuration_error_without_echoing_value(
    monkeypatch, variable, value
):
    monkeypatch.setenv(variable, value)

    with pytest.raises(ConfigurationError) as raised:
        load_settings()

    message = str(raised.value)
    assert variable in message
    assert value not in message.replace(variable, "")
    for leak in ("staging", "verbose", "MARCADOR-URL", "trinta"):
        assert leak not in message


@pytest.mark.req("RNF-04")
def test_multiple_errors_are_all_listed(monkeypatch):
    monkeypatch.setenv("COFRE_ENV", "staging")
    monkeypatch.setenv("COFRE_LOGIN_MAX_ATTEMPTS", "0")

    with pytest.raises(ConfigurationError) as raised:
        load_settings()

    assert "COFRE_ENV" in str(raised.value)
    assert "COFRE_LOGIN_MAX_ATTEMPTS" in str(raised.value)


def test_invalid_database_url_is_rejected(monkeypatch):
    monkeypatch.setenv("COFRE_DATABASE_URL", "::not a url::")

    with pytest.raises(ConfigurationError, match="COFRE_DATABASE_URL"):
        load_settings()


def test_explicit_settings_accept_test_values():
    settings = Settings(env="test", argon2_memory_kib=1024, argon2_time_cost=1)

    assert settings.argon2_memory_kib == 1024


@pytest.mark.req("RNF-04")
def test_configuration_error_does_not_chain_validation_error(monkeypatch):
    # A chained pydantic ValidationError would print input_value in the startup traceback.
    monkeypatch.setenv("COFRE_ENV", "staging")

    with pytest.raises(ConfigurationError) as raised:
        load_settings()

    assert raised.value.__cause__ is None
    assert raised.value.__suppress_context__


@pytest.mark.req("RNF-04")
def test_malformed_url_with_password_is_not_echoed(monkeypatch):
    # make_url raises ValueError quoting part of the URL for a non-numeric port.
    monkeypatch.setenv("COFRE_DATABASE_URL", "postgresql://user:p@ss:w0rd@host/db")

    with pytest.raises(ConfigurationError, match="COFRE_DATABASE_URL") as raised:
        load_settings()

    assert "w0rd" not in str(raised.value)
    assert "host" not in str(raised.value)
