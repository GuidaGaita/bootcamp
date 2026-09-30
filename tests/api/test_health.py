import pytest
from fastapi.testclient import TestClient

from cofre.main import create_app
from tests.conftest import make_settings, sqlite_url
from tests.support.contract import assert_response_matches

pytestmark = [pytest.mark.api, pytest.mark.req("RF-01")]

LEAKS = ("sqlite", "Traceback", "OperationalError", "Error:", ".db")


def _assert_unavailable(response, tmp_path):
    assert response.status_code == 503
    assert_response_matches(response, operation=("get", "/health"))
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
    for leak in (*LEAKS, str(tmp_path), tmp_path.as_posix()):
        assert leak not in response.text


def test_health_returns_ok_when_database_is_available(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert_response_matches(response, operation=("get", "/health"))


def test_health_does_not_require_authorization(client):
    response = client.get("/health")

    assert "authorization" not in {name.lower() for name in response.request.headers}
    assert response.status_code == 200


def test_health_returns_503_without_internal_details(tmp_path, clock):
    app = create_app(make_settings(tmp_path, database_url=sqlite_url(tmp_path)), clock)

    with TestClient(app) as client:
        response = client.get("/health")

    _assert_unavailable(response, tmp_path)


def test_app_starts_with_unavailable_database_and_answers_503(tmp_path, clock):
    blocker = tmp_path / "blocked"
    blocker.write_text("not a directory", encoding="utf-8")
    app = create_app(make_settings(tmp_path, database_url=sqlite_url(blocker / "cofre.db")), clock)

    with TestClient(app) as client:
        response = client.get("/health")

    _assert_unavailable(response, tmp_path)


def test_health_reflects_recovery_without_restart(tmp_path, clock):
    parent = tmp_path / "data"
    parent.write_text("file standing in for the directory", encoding="utf-8")
    app = create_app(make_settings(tmp_path, database_url=sqlite_url(parent / "cofre.db")), clock)

    with TestClient(app) as client:
        assert client.get("/health").status_code == 503

        parent.unlink()
        parent.mkdir()
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
