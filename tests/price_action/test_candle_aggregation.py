# =============================================================================
# File: test_candle_aggregation.py
# Purpose: Tests historical candle aggregation and interval boundaries.
# =============================================================================

from datetime import datetime, timedelta, timezone

import pytest

from stonks.models.candle_data import CandleData
from stonks.models.research_interval import ResearchInterval
from stonks.price_action.candle_aggregation import aggregate_candles


def make_candle(
    timestamp: datetime,
    price: float,
    volume: int = 100,
) -> CandleData:
    """Create a deterministic source candle."""
    return CandleData(
        timestamp=timestamp,
        open_price=price,
        high_price=price + 2,
        low_price=price - 1,
        close_price=price + 1,
        volume=volume,
    )


def test_ten_minute_aggregation() -> None:
    """Aggregate ten source candles into one accurate OHLCV candle."""
    start = datetime(2026, 9, 25, 13, 30, tzinfo=timezone.utc)

    candles = [make_candle(start + timedelta(minutes=i), 100 + i) for i in range(10)]

    results = aggregate_candles(
        candles,
        ResearchInterval.TEN_MINUTES,
        ResearchInterval.ONE_MINUTE,
    )

    assert len(results) == 1

    result = results[0]
    candle = result.candle

    assert candle.open_price == 100
    assert candle.high_price == 111
    assert candle.low_price == 99
    assert candle.close_price == 110
    assert candle.volume == 1000
    assert candle.timestamp == start
    assert result.source_count == 10
    assert not result.has_missing_source_candles


def test_missing_minute_is_reported() -> None:
    """Incomplete minute buckets must not be presented as complete."""
    start = datetime(2026, 9, 25, 13, 30, tzinfo=timezone.utc)

    candles = [make_candle(start + timedelta(minutes=i), 100) for i in range(10) if i != 4]

    results = aggregate_candles(
        candles,
        ResearchInterval.TEN_MINUTES,
        ResearchInterval.ONE_MINUTE,
    )

    assert len(results) == 1
    assert results[0].source_count == 9
    assert results[0].expected_count == 10
    assert results[0].has_missing_source_candles


def test_weekly_aggregation() -> None:
    """Daily candles from the same week form one weekly candle."""
    monday = datetime(2026, 9, 21, tzinfo=timezone.utc)

    candles = [make_candle(monday + timedelta(days=i), 100 + i) for i in range(5)]

    results = aggregate_candles(
        candles,
        ResearchInterval.WEEKLY,
        ResearchInterval.DAILY,
    )

    assert len(results) == 1
    assert results[0].candle.timestamp == monday
    assert results[0].candle.open_price == 100
    assert results[0].candle.close_price == 105
    assert results[0].candle.volume == 500
    assert results[0].expected_count is None


def test_quarterly_aggregation() -> None:
    """Daily candles in the same quarter share a calendar bucket."""
    candles = [
        make_candle(datetime(2026, 1, 5, tzinfo=timezone.utc), 100),
        make_candle(datetime(2026, 2, 5, tzinfo=timezone.utc), 110),
        make_candle(datetime(2026, 3, 5, tzinfo=timezone.utc), 120),
        make_candle(datetime(2026, 4, 5, tzinfo=timezone.utc), 130),
    ]

    results = aggregate_candles(
        candles,
        ResearchInterval.QUARTERLY,
        ResearchInterval.DAILY,
    )

    assert len(results) == 2

    assert results[0].candle.timestamp == datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert results[0].candle.open_price == 100
    assert results[0].candle.close_price == 121
    assert results[0].candle.volume == 300

    assert results[1].candle.timestamp == datetime(2026, 4, 1, tzinfo=timezone.utc)


def test_rejects_wrong_source_interval() -> None:
    """Calendar candles cannot be built from arbitrary minute candles."""
    candles = [
        make_candle(
            datetime(2026, 9, 25, 13, 30, tzinfo=timezone.utc),
            100,
        )
    ]

    with pytest.raises(ValueError):
        aggregate_candles(
            candles,
            ResearchInterval.WEEKLY,
            ResearchInterval.ONE_MINUTE,
        )


def test_rejects_duplicate_timestamps() -> None:
    """Duplicate source candles must not inflate volume."""
    timestamp = datetime(2026, 9, 25, 13, 30, tzinfo=timezone.utc)
    candles = [make_candle(timestamp, 100), make_candle(timestamp, 100)]

    with pytest.raises(ValueError):
        aggregate_candles(
            candles,
            ResearchInterval.FIVE_MINUTES,
            ResearchInterval.ONE_MINUTE,
        )


def test_empty_input() -> None:
    """Empty input produces no artificial candles."""
    assert (
        aggregate_candles(
            [],
            ResearchInterval.MONTHLY,
            ResearchInterval.DAILY,
        )
        == []
    )
