"""HTTP edge concentrated in a single pure ASGI middleware (ADR-0015, research R4)."""

import re
import uuid
from collections.abc import Iterable

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

REQUEST_ID_HEADER = b"x-request-id"
_REQUEST_ID_PATTERN = re.compile(r"[A-Za-z0-9-]{1,64}", re.ASCII)


def choose_request_id(raw_headers: Iterable[tuple[bytes, bytes]]) -> str:
    """Propagate a single valid ``X-Request-ID``; otherwise generate a UUID v4 (research R11)."""
    values = [value for name, value in raw_headers if name.lower() == REQUEST_ID_HEADER]
    if len(values) == 1:
        candidate = values[0].decode("latin-1")
        if _REQUEST_ID_PATTERN.fullmatch(candidate):
            return candidate
    return str(uuid.uuid4())


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = choose_request_id(scope.get("headers", []))
        scope.setdefault("state", {})["request_id"] = request_id

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-Request-ID"] = request_id
            await send(message)

        await self.app(scope, receive, send_with_headers)
