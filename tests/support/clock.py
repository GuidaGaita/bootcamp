"""Controllable clock for tests (research R9)."""

from datetime import UTC, datetime, timedelta

DEFAULT_START = datetime(2026, 1, 1, tzinfo=UTC)


def _require_aware(instant: datetime) -> datetime:
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("O instante precisa ter fuso horário.")
    return instant.astimezone(UTC)


class FakeClock:
    """Clock that only moves when told to."""

    def __init__(self, start: datetime = DEFAULT_START) -> None:
        self._now = _require_aware(start)

    def now(self) -> datetime:
        return self._now

    def advance(self, **kwargs: float) -> None:
        self._now += timedelta(**kwargs)

    def set(self, instant: datetime) -> None:
        self._now = _require_aware(instant)
