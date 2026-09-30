"""No request data in logs (FR-014, docs/04 §5)."""

import asyncio
import logging

import pytest

pytestmark = [pytest.mark.security, pytest.mark.req("RNF-04", "RNF-13")]

HEADERS = {
    "Authorization": "Bearer MARCADOR-TOKEN",
    "Cookie": "s=MARCADOR-COOKIE",
}


async def _call(app, method: str, path: str, query: bytes, body: bytes) -> list[dict]:
    """Drive the ASGI app directly: HTTP clients refuse a header value with a newline."""
    headers = [(name.lower().encode(), value.encode()) for name, value in HEADERS.items()]
    headers += [(b"x-request-id", b"MARCADOR\nINJETADO"), (b"content-type", b"application/json")]
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "root_path": "",
        "query_string": query,
        "headers": headers,
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }
    messages = [{"type": "http.request", "body": body, "more_body": False}]
    sent: list[dict] = []

    async def receive() -> dict:
        return messages.pop(0) if messages else {"type": "http.disconnect"}

    async def send(message: dict) -> None:
        sent.append(message)

    await app(scope, receive, send)
    return sent


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("POST", "/api/v1/_probe/echo", b'{"name": "MARCADOR-CORPO"}'),
        ("GET", "/api/v1/rota-inexistente", b""),
    ],
)
def test_sensitive_request_data_never_reaches_logs(app, caplog, capsys, method, path, body):
    with caplog.at_level(logging.DEBUG):
        sent = asyncio.run(_call(app, method, path, b"q=MARCADOR-QUERY", body))

    start = next(message for message in sent if message["type"] == "http.response.start")
    request_id = dict(start["headers"])[b"x-request-id"]
    assert b"MARCADOR" not in request_id
    assert any(getattr(r, "event", None) == "request" for r in caplog.records)
    captured = capsys.readouterr()
    for text in (caplog.text, captured.out, captured.err):
        assert "MARCADOR" not in text
