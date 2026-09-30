import pytest

from cofre.core.errors import CofreError, ServiceUnavailableError
from cofre.repositories.database import build_engine
from cofre.services.health import HealthService, HealthStatus
from tests.conftest import sqlite_url

pytestmark = [pytest.mark.integration, pytest.mark.req("RF-01")]


def test_check_returns_ok_with_reachable_database(tmp_path):
    engine = build_engine(sqlite_url(tmp_path / "cofre.db"))
    try:
        assert HealthService(engine).check() is HealthStatus.OK
    finally:
        engine.dispose()


def test_check_raises_service_unavailable_with_unreachable_database(tmp_path):
    engine = build_engine(sqlite_url(tmp_path))
    try:
        with pytest.raises(ServiceUnavailableError) as raised:
            HealthService(engine).check()
    finally:
        engine.dispose()

    assert isinstance(raised.value, CofreError)
    assert raised.value.code == "SERVICE_UNAVAILABLE"
    assert raised.value.status == 503
