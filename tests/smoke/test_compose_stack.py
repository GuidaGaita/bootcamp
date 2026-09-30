import time

import httpx
import pytest

from tests.smoke.conftest import REPO_ROOT, compose

pytestmark = pytest.mark.smoke


@pytest.mark.req("RF-01", "RNF-10")
def test_health_answers_ok_with_request_id(compose_stack):
    response = httpx.get(f"{compose_stack}/health", timeout=10)

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"]


@pytest.mark.req("RNF-08", "RNF-10")
def test_docs_are_served(compose_stack):
    response = httpx.get(f"{compose_stack}/docs", timeout=10)

    assert response.status_code == 200


@pytest.mark.req("RNF-10", "RNF-15")
def test_api_runs_as_non_root(compose_stack):
    result = compose("exec", "-T", "api", "id", "-u")

    assert result.stdout.strip() != "0"


@pytest.mark.req("RNF-10")
def test_database_survives_restart(compose_stack):
    assert httpx.get(f"{compose_stack}/health", timeout=10).status_code == 200
    compose("exec", "-T", "api", "test", "-f", "/data/cofre.db")

    compose("restart", "api")
    compose("up", "-d", "--wait", "api")

    compose("exec", "-T", "api", "test", "-f", "/data/cofre.db")


@pytest.mark.req("RNF-10")
def test_tests_service_writes_reports_to_host(compose_stack):
    junit = REPO_ROOT / "reports" / "junit.xml"
    started = time.time()

    compose("run", "--rm", "--build", "tests", "pytest", "tests/unit/test_clock.py", "--no-cov")

    assert junit.is_file()
    assert junit.stat().st_mtime >= started - 1
