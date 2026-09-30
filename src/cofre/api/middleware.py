"""HTTP edge concentrated in a single pure ASGI middleware (ADR-0015, research R4)."""

import logging
import re
import uuid
from collections.abc import Iterable

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from cofre.api.errors import error_response

logger = logging.getLogger("cofre")

REQUEST_ID_HEADER = b"x-request-id"
_REQUEST_ID_PATTERN = re.compile(r"[A-Za-z0-9-]{1,64}", re.ASCII)
_API_PREFIX = "/api/v1"


def choose_request_id(raw_headers: Iterable[tuple[bytes, bytes]]) -> str:
    """Propagate a single valid ``X-Request-ID``; otherwise generate a UUID v4 (research R11)."""
    values = [value for name, value in raw_headers if name.lower() == REQUEST_ID_HEADER]
    if len(values) == 1:
        candidate = values[0].decode("latin-1")
        if _REQUEST_ID_PATTERN.fullmatch(candidate):
            return candidate
    return str(uuid.uuid4())


def is_api_path(path: str) -> bool:
    """``/api/v1`` itself or anything below it, but not ``/api/v10`` (research R12)."""
    return path == _API_PREFIX or path.startswith(_API_PREFIX + "/")


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = choose_request_id(scope.get("headers", []))
        scope.setdefault("state", {})["request_id"] = request_id
        no_store = is_api_path(scope["path"])
        response_started = False

        async def send_with_headers(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
                headers = MutableHeaders(scope=message)
                headers["X-Request-ID"] = request_id
                if no_store:
                    headers["Cache-Control"] = "no-store"
            await send(message)

        try:
            await self.app(scope, receive, send_with_headers)
        except Exception as exc:
            logger.error(
                "unhandled_exception",
                extra={"event": "unhandled_exception", "error_type": type(exc).__name__},
            )
            if response_started:
                return
            response = error_response("INTERNAL_ERROR")
            await response(scope, receive, send_with_headers)
