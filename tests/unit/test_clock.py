from datetime import UTC, datetime, timedelta

import pytest

from cofre.core.clock import Clock, SystemClock
from tests.support.clock import FakeClock

pytestmark = [pytest.mark.unit, pytest.mark.req("RNF-09")]


def test_system_clock_returns_aware_utc_datetime():
    now = SystemClock().now()

    assert now.tzinfo is not None
    assert now.utcoffset() == timedelta(0)


def test_system_clock_satisfies_clock_protocol():
    clock: Clock = SystemClock()

    assert isinstance(clock.now(), datetime)


def test_fake_clock_starts_at_fixed_instant():
    assert FakeClock().now() == datetime(2026, 1, 1, tzinfo=UTC)


def test_fake_clock_does_not_move_by_itself():
    clock = FakeClock()

    assert clock.now() == clock.now()


def test_fake_clock_advance_moves_forward():
    clock = FakeClock()

    clock.advance(minutes=30)

    assert clock.now() == datetime(2026, 1, 1, 0, 30, tzinfo=UTC)


def test_fake_clock_set_changes_instant():
    clock = FakeClock()
    instant = datetime(2027, 5, 1, 12, tzinfo=UTC)

    clock.set(instant)

    assert clock.now() == instant


def test_fake_clock_set_rejects_naive_datetime():
    clock = FakeClock()

    with pytest.raises(ValueError, match="fuso"):
        clock.set(datetime(2027, 5, 1, 12))


def test_fake_clock_rejects_naive_start():
    with pytest.raises(ValueError, match="fuso"):
        FakeClock(datetime(2027, 5, 1, 12))
