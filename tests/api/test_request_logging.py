import json
import logging
import uuid

import pytest
from fastapi.testclient import TestClient

from cofre.core.logging import JsonFormatter
from cofre.main import create_app
from tests.conftest import make_settings
from tests.support import probe

pytestmark = [pytest.mark.api, pytest.mark.req("RNF-13")]


def _records(caplog, event: str) -> list[logging.LogRecord]:
    return [r for r in caplog.records if getattr(r, "event", None) == event]


def _request_log(caplog) -> dict:
    (record,) = _records(caplog, "request")
    return json.loads(JsonFormatter().format(record))


def test_valid_request_id_is_echoed_and_logged(client, caplog):
    with caplog.at_level(logging.INFO, logger="cofre"):
        response = client.get("/health", headers={"X-Request-ID": "abc-123"})

    assert response.headers["X-Request-ID"] == "abc-123"
    assert _request_log(caplog)["request_id"] == "abc-123"


def test_missing_request_id_generates_same_uuid_in_header_and_log(client, caplog):
    with caplog.at_level(logging.INFO, logger="cofre"):
        response = client.get("/health")

    request_id = response.headers["X-Request-ID"]
    assert uuid.UUID(request_id).version == 4
    assert _request_log(caplog)["request_id"] == request_id


def test_duplicated_request_id_headers_generate_uuid(client):
    response = client.get("/health", headers=[("X-Request-ID", "a-1"), ("X-Request-ID", "b-2")])

    assert uuid.UUID(response.headers["X-Request-ID"]).version == 4


@pytest.mark.parametrize(
    ("method", "path", "kwargs"),
    [
        ("GET", "/health", {}),
        ("GET", "/docs", {}),
        ("GET", "/openapi.json", {}),
        ("GET", "/api/v1/rota-inexistente", {}),
        ("POST", "/health", {}),
        ("POST", "/api/v1/_probe/echo", {"json": {}}),
        ("GET", "/api/v1/_probe/boom", {}),
    ],
)
def test_every_response_has_request_id(client, method, path, kwargs):
    response = client.request(method, path, **kwargs)

    assert response.headers["X-Request-ID"]


def test_one_request_record_per_call_with_fields(client, caplog):
    with caplog.at_level(logging.INFO, logger="cofre"):
        client.get("/health")

    data = _request_log(caplog)
    assert data["level"] == "INFO"
    assert data["method"] == "GET"
    assert data["status"] == 200
    assert data["route"] == "/health"
    assert data["duration_ms"] >= 0


def test_route_is_null_for_unknown_path(client, caplog):
    with caplog.at_level(logging.INFO, logger="cofre"):
        client.get("/api/v1/rota-inexistente")

    data = _request_log(caplog)
    assert data["route"] is None
    assert data["status"] == 404


def test_timestamp_comes_from_application_clock(client, clock, caplog):
    clock.advance(minutes=5)

    with caplog.at_level(logging.INFO, logger="cofre"):
        client.get("/health")

    assert _request_log(caplog)["timestamp"].startswith("2026-01-01T00:05:00")


def test_configured_level_above_info_suppresses_request_records(tmp_path, clock, caplog):
    app = create_app(make_settings(tmp_path, log_level="WARNING"), clock)

    with caplog.at_level(logging.DEBUG, logger="cofre"), TestClient(app) as client:
        client.get("/health")

    assert _records(caplog, "request") == []


@pytest.mark.req("RNF-04")
def test_unhandled_exception_is_logged_without_message(client, caplog):
    with caplog.at_level(logging.INFO, logger="cofre"):
        response = client.get("/api/v1/_probe/boom")

    (record,) = _records(caplog, "unhandled_exception")
    data = json.loads(JsonFormatter().format(record))
    assert record.levelno == logging.ERROR
    assert data["error_type"] == "RuntimeError"
    assert data["stack"]
    assert data["request_id"] == response.headers["X-Request-ID"]
    assert "MARCADOR-EXCECAO" not in caplog.text
    assert _request_log(caplog)["status"] == 500


@pytest.mark.req("RNF-04")
def test_probe_router_is_only_in_test_app(tmp_path, clock):
    app = create_app(make_settings(tmp_path), clock)

    with TestClient(app) as client:
        response = client.get(f"{probe.router.prefix}/boom")

    assert response.status_code == 404
