"""Injectable clock (research R9)."""

from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    """Source of the current instant, always timezone-aware in UTC."""

    def now(self) -> datetime: ...


class SystemClock:
    """Clock backed by the operating system."""

    def now(self) -> datetime:
        return datetime.now(UTC)
