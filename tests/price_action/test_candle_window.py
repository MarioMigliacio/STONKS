# =============================================================================
# File: test_candle_window.py
# Purpose: Tests historical candle time-window selection.
# =============================================================================

from datetime import datetime, timedelta, timezone

import pytest

from stonks.models.candle_data import CandleData
from stonks.price_action.candle_window import select_candle_window


def make_candle(timestamp: datetime) -> CandleData:
    """Create a deterministic test candle."""
    return CandleData(
        timestamp=timestamp,
        open_price=100.0,
        high_price=102.0,
        low_price=99.0,
        close_price=101.0,
        volume=1000,
    )


def test_selects_requested_window() -> None:
    """Include the start boundary and exclude the end boundary."""
    start = datetime(2026, 9, 25, 13, 30, tzinfo=timezone.utc)

    candles = [make_candle(start + timedelta(minutes=index)) for index in range(10)]

    selected = select_candle_window(
        candles,
        start,
        start + timedelta(minutes=5),
    )

    assert len(selected) == 5
    assert selected[0].timestamp == start
    assert selected[-1].timestamp == start + timedelta(minutes=4)


def test_returns_candles_chronologically() -> None:
    """Normalize input ordering without modifying the source."""
    start = datetime(2026, 9, 25, 13, 30, tzinfo=timezone.utc)

    candles = [
        make_candle(start + timedelta(minutes=2)),
        make_candle(start),
        make_candle(start + timedelta(minutes=1)),
    ]

    selected = select_candle_window(
        candles,
        start,
        start + timedelta(minutes=3),
    )

    assert [candle.timestamp for candle in selected] == [
        start,
        start + timedelta(minutes=1),
        start + timedelta(minutes=2),
    ]


def test_empty_window_returns_empty_list() -> None:
    """An interval without candles should return no data."""
    start = datetime(2026, 9, 25, 13, 30, tzinfo=timezone.utc)

    selected = select_candle_window(
        [],
        start,
        start + timedelta(minutes=5),
    )

    assert selected == []


def test_rejects_invalid_window() -> None:
    """The start must precede the end."""
    start = datetime(2026, 9, 25, 13, 30, tzinfo=timezone.utc)

    with pytest.raises(ValueError):
        select_candle_window([], start, start)


def test_rejects_naive_timestamps() -> None:
    """Timezone-naive timestamps must not be accepted."""
    start = datetime(2026, 9, 25, 13, 30)

    with pytest.raises(ValueError):
        select_candle_window(
            [],
            start,
            start + timedelta(minutes=5),
        )
