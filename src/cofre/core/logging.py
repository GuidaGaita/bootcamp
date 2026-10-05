"""Structured JSON logs without sensitive data (research R10, FR-013 to FR-015)."""

import json
import logging
import sys
import traceback
from datetime import UTC, datetime
from types import TracebackType

from cofre.core.clock import Clock

LOGGER_NAME = "cofre"

# Only these record attributes are ever written; anything else is dropped (FR-014).
ALLOWED_FIELDS = (
    "request_id",
    "credential_id",
    "method",
    "route",
    "status",
    "duration_ms",
    "error_type",
    "stack",
)


def format_stack(tb: TracebackType | None) -> list[str]:
    """``file:line:function`` frames, never the exception message."""
    return [f"{frame.filename}:{frame.lineno}:{frame.name}" for frame in traceback.extract_tb(tb)]


def _iso(instant: datetime) -> str:
    return instant.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class JsonFormatter(logging.Formatter):
    """One JSON object per line with a fixed set of fields."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = getattr(record, "timestamp", None)
        if not isinstance(timestamp, datetime):
            timestamp = datetime.fromtimestamp(record.created, UTC)
        data: dict[str, object] = {
            "timestamp": _iso(timestamp),
            "level": record.levelname,
            "event": getattr(record, "event", None) or str(record.msg),
        }
        for field in ALLOWED_FIELDS:
            if hasattr(record, field):
                data[field] = getattr(record, field)
        if record.exc_info and record.exc_info[0] is not None:
            data.setdefault("error_type", record.exc_info[0].__name__)
            data.setdefault("stack", format_stack(record.exc_info[2]))
        return json.dumps(data, ensure_ascii=False, default=str)


def log_event(
    configured_level: str, clock: Clock, level: int, event: str, **fields: object
) -> None:
    """Emit ``event`` only if the application's configured level allows it (FR-016, FR-022)."""
    if level < logging.getLevelNamesMapping()[configured_level]:
        return
    logging.getLogger(LOGGER_NAME).log(
        level, event, extra={"event": event, "timestamp": clock.now(), **fields}
    )


def configure_logging() -> None:
    """Install the JSON handler on the ``cofre`` logger once per process."""
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    if any(isinstance(handler.formatter, JsonFormatter) for handler in logger.handlers):
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
