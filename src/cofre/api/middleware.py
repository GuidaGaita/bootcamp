"""HTTP edge concentrated in a single pure ASGI middleware (ADR-0015, research R4)."""

import logging
import re
import time
import uuid
from collections.abc import Iterable

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from cofre.api.errors import error_response
from cofre.core.logging import format_stack, log_event

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
    """Request ID, cross-cutting headers, standard 500 and one log line per request."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        started = time.perf_counter()
        request_id = choose_request_id(scope.get("headers", []))
        scope.setdefault("state", {})["request_id"] = request_id
        no_store = is_api_path(scope["path"])
        status: int | None = None

        async def send_with_headers(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                headers = MutableHeaders(scope=message)
                headers["X-Request-ID"] = request_id
                if no_store:
                    headers["Cache-Control"] = "no-store"
            await send(message)

        try:
            await self.app(scope, receive, send_with_headers)
        except Exception as exc:
            self._log(
                scope,
                logging.ERROR,
                "unhandled_exception",
                request_id=request_id,
                error_type=type(exc).__name__,
                stack=format_stack(exc.__traceback__),
            )
            if status is None:
                await error_response("INTERNAL_ERROR")(scope, receive, send_with_headers)
        finally:
            route = scope.get("route")
            self._log(
                scope,
                logging.INFO,
                "request",
                request_id=request_id,
                method=scope["method"],
                route=getattr(route, "path", None),
                status=status,
                duration_ms=round((time.perf_counter() - started) * 1000, 3),
            )

    @staticmethod
    def _log(scope: Scope, level: int, event: str, **fields: object) -> None:
        state = scope["app"].state
        log_event(state.settings.log_level, state.clock, level, event, **fields)
