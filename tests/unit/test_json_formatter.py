import json
import logging
import sys
from datetime import UTC, datetime

import pytest

from cofre.core.logging import JsonFormatter, configure_logging

pytestmark = [pytest.mark.unit, pytest.mark.req("RNF-13")]


def _record(msg="request", exc_info=None, **extra) -> logging.LogRecord:
    record = logging.LogRecord("cofre", logging.INFO, __file__, 10, msg, None, exc_info)
    record.created = datetime(2026, 3, 4, 5, 6, 7, 890000, tzinfo=UTC).timestamp()
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def _format(record) -> dict:
    output = JsonFormatter().format(record)
    assert "\n" not in output
    return json.loads(output)


def test_record_becomes_single_json_line_with_required_fields():
    data = _format(_record(event="request", request_id="abc-123", status=200))

    assert data["level"] == "INFO"
    assert data["event"] == "request"
    assert data["request_id"] == "abc-123"
    assert data["status"] == 200
    assert data["timestamp"] == "2026-03-04T05:06:07.890Z"


def test_timestamp_from_extra_takes_precedence():
    instant = datetime(2026, 1, 1, 0, 5, tzinfo=UTC)

    data = _format(_record(event="request", timestamp=instant))

    assert datetime.fromisoformat(data["timestamp"]) == instant


def test_event_defaults_to_message_name():
    assert _format(_record("database_init_failed"))["event"] == "database_init_failed"


def test_unknown_extra_fields_are_dropped():
    data = _format(_record(event="request", body="MARCADOR-CORPO", query="MARCADOR-QUERY"))

    assert "MARCADOR" not in json.dumps(data)


def test_exception_stack_is_recorded_without_message():
    try:
        raise RuntimeError("MARCADOR-EXCECAO")
    except RuntimeError:
        exc_info = sys.exc_info()

    output = JsonFormatter().format(_record("unhandled_exception", exc_info=exc_info))
    data = json.loads(output)

    assert "MARCADOR-EXCECAO" not in output
    assert data["error_type"] == "RuntimeError"
    assert data["stack"]
    file, line, function = data["stack"][-1].rsplit(":", 2)
    assert file.endswith("test_json_formatter.py")
    assert int(line) > 0
    assert function == "test_exception_stack_is_recorded_without_message"


def test_configure_logging_is_idempotent():
    logger = logging.getLogger("cofre")

    configure_logging()
    configure_logging()

    handlers = [h for h in logger.handlers if isinstance(h.formatter, JsonFormatter)]
    assert len(handlers) == 1
