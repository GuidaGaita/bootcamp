import pytest

from tests.support.contract import assert_response_matches

pytestmark = [pytest.mark.api, pytest.mark.req("RNF-08", "RNF-14")]


def _error(response) -> dict:
    return response.json()["error"]


def test_unknown_route_returns_standard_not_found(client):
    response = client.get("/api/v1/rota-inexistente")

    assert response.status_code == 404
    assert_response_matches(response, component="NotFound")
    assert _error(response)["message"] == "Recurso não encontrado."


def test_unsupported_method_returns_method_not_allowed_with_allow_header(client):
    response = client.post("/health")

    assert response.status_code == 405
    assert_response_matches(response, component="MethodNotAllowed")
    assert response.headers["Allow"] == "GET"


def test_malformed_json_returns_validation_error_on_body(client):
    response = client.post(
        "/api/v1/_probe/echo",
        content=b'{"name": ',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422
    assert_response_matches(response, component="ValidationError")
    assert _error(response)["details"] == [{"field": "body", "issue": "JSON malformado."}]


def test_missing_field_returns_validation_error_with_field_name(client):
    response = client.post("/api/v1/_probe/echo", json={})

    assert response.status_code == 422
    assert_response_matches(response, component="ValidationError")
    assert _error(response)["details"] == [{"field": "name", "issue": "Campo obrigatório."}]


@pytest.mark.req("RNF-04")
def test_validation_error_does_not_echo_received_value(client):
    response = client.post("/api/v1/_probe/echo", json={"name": ["MARCADOR-VALOR"]})

    assert response.status_code == 422
    assert_response_matches(response, component="ValidationError")
    assert "MARCADOR-VALOR" not in response.text


@pytest.mark.req("RNF-04")
def test_unhandled_exception_returns_generic_internal_error(client):
    response = client.get("/api/v1/_probe/boom")

    assert response.status_code == 500
    assert_response_matches(response, component="InternalError")
    for leak in ("MARCADOR-EXCECAO", "RuntimeError", "Traceback"):
        assert leak not in response.text
