import httpx
import pytest

from tests.support.contract import ContractViolation, assert_response_matches

pytestmark = [pytest.mark.unit, pytest.mark.req("RNF-08")]

HEADERS = {"X-Request-ID": "abc-123"}


def _response(status: int, body: object, headers: dict[str, str] | None = None) -> httpx.Response:
    return httpx.Response(status, json=body, headers=HEADERS if headers is None else headers)


def test_accepts_valid_health_response():
    assert_response_matches(_response(200, {"status": "ok"}), operation=("get", "/health"))


def test_rejects_extra_field():
    with pytest.raises(ContractViolation):
        assert_response_matches(
            _response(200, {"status": "ok", "version": "1"}), operation=("get", "/health")
        )


def test_rejects_undeclared_status():
    with pytest.raises(ContractViolation):
        assert_response_matches(_response(418, {"status": "ok"}), operation=("get", "/health"))


def test_accepts_service_unavailable_via_response_ref():
    body = {"error": {"code": "SERVICE_UNAVAILABLE", "message": "x"}}

    assert_response_matches(_response(503, body), operation=("get", "/health"))


def test_rejects_details_outside_validation_error():
    body = {"error": {"code": "NOT_FOUND", "message": "x", "details": [{"field": "a", "issue": "b"}]}}

    with pytest.raises(ContractViolation):
        assert_response_matches(_response(404, body), component="NotFound")


def test_requires_details_on_validation_error():
    body = {"error": {"code": "VALIDATION_ERROR", "message": "x"}}

    with pytest.raises(ContractViolation):
        assert_response_matches(_response(422, body), component="ValidationError")


def test_rejects_code_different_from_component():
    body = {"error": {"code": "INTERNAL_ERROR", "message": "x"}}

    with pytest.raises(ContractViolation):
        assert_response_matches(_response(404, body), component="NotFound")


def test_fails_when_required_header_is_missing():
    with pytest.raises(ContractViolation, match="X-Request-ID"):
        assert_response_matches(
            _response(200, {"status": "ok"}, headers={}), operation=("get", "/health")
        )


def test_rejects_header_violating_schema():
    with pytest.raises(ContractViolation, match="X-Request-ID"):
        assert_response_matches(
            _response(200, {"status": "ok"}, headers={"X-Request-ID": "a b"}),
            operation=("get", "/health"),
        )


def test_requires_exactly_one_target():
    with pytest.raises(ValueError):
        assert_response_matches(_response(200, {"status": "ok"}))
