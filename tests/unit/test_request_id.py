import uuid

import pytest

from cofre.api.middleware import choose_request_id

pytestmark = [pytest.mark.unit, pytest.mark.req("RNF-13", "RNF-04")]


def _headers(*values: bytes) -> list[tuple[bytes, bytes]]:
    return [(b"accept", b"*/*"), *((b"x-request-id", value) for value in values)]


def _is_uuid4(value: str) -> bool:
    return uuid.UUID(value).version == 4


@pytest.mark.parametrize("value", ["abc-123", "a" * 64, "A-z-0-9"])
def test_valid_single_header_is_propagated(value):
    assert choose_request_id(_headers(value.encode("ascii"))) == value


def test_header_name_is_case_insensitive():
    assert choose_request_id([(b"X-Request-ID", b"abc-123")]) == "abc-123"


@pytest.mark.parametrize(
    "value",
    [b"a" * 65, b"", b"abc\n123", b"abc 123", "ação".encode("latin-1"), "ação".encode()],
    ids=["too-long", "empty", "newline", "space", "latin1", "utf8"],
)
def test_invalid_value_generates_new_uuid4(value):
    request_id = choose_request_id(_headers(value))

    assert _is_uuid4(request_id)
    assert request_id != value.decode("latin-1")


def test_missing_header_generates_uuid4():
    assert _is_uuid4(choose_request_id(_headers()))


def test_duplicated_header_generates_uuid4():
    request_id = choose_request_id(_headers(b"abc-123", b"def-456"))

    assert _is_uuid4(request_id)


def test_generated_ids_are_unique():
    assert choose_request_id([]) != choose_request_id([])
