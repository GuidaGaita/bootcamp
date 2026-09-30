import pytest

from tests.conftest import make_settings

pytestmark = [pytest.mark.unit, pytest.mark.req("RNF-09")]


def test_make_settings_ignores_developer_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("COFRE_LOG_LEVEL", "WARNING")
    monkeypatch.setenv("COFRE_SESSION_TTL_MINUTES", "99")

    settings = make_settings(tmp_path)

    assert settings.log_level == "INFO"
    assert settings.session_ttl_minutes == 30
    assert settings.env == "test"
