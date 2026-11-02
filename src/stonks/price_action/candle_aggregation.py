# =============================================================================
# File: candle_aggregation.py
# Purpose: Aggregates normalized OHLCV candles into research intervals.
# =============================================================================

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from stonks.models.candle_data import CandleData
from stonks.models.research_interval import ResearchInterval

EASTERN = ZoneInfo("America/New_York")

MINUTE_INTERVALS = {
    ResearchInterval.ONE_MINUTE: 1,
    ResearchInterval.FIVE_MINUTES: 5,
    ResearchInterval.TEN_MINUTES: 10,
    ResearchInterval.FIFTEEN_MINUTES: 15,
    ResearchInterval.THIRTY_MINUTES: 30,
    ResearchInterval.SIXTY_MINUTES: 60,
}


@dataclass(frozen=True)
class AggregatedCandle:
    """
    Represents an aggregated candle and its source coverage.

    Attributes:
        candle:
            Aggregated OHLCV candle.

        source_count:
            Number of source candles included.

        expected_count:
            Expected count for minute-based aggregation,
            or None for calendar-based aggregation.
    """

    candle: CandleData
    source_count: int
    expected_count: Optional[int]

    @property
    def has_missing_source_candles(self) -> bool:
        """Identify missing minute candles within an aggregation bucket."""
        return self.expected_count is not None and self.source_count < self.expected_count


def _validate_candles(candles: list[CandleData]) -> None:
    """Require timezone-aware timestamps and unique candle starts."""
    timestamps = set()

    for candle in candles:
        timestamp = candle.timestamp

        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("Candle timestamps must be timezone-aware.")

        utc_timestamp = timestamp.astimezone(timezone.utc)

        if utc_timestamp in timestamps:
            raise ValueError("Duplicate source candle timestamp.")

        timestamps.add(utc_timestamp)


def _minute_bucket(
    timestamp: datetime,
    interval_minutes: int,
) -> datetime:
    """Align an intraday candle to an Eastern Time clock interval."""
    eastern = timestamp.astimezone(EASTERN)

    minutes = eastern.hour * 60 + eastern.minute
    aligned_minutes = (minutes // interval_minutes) * interval_minutes

    return eastern.replace(
        hour=aligned_minutes // 60,
        minute=aligned_minutes % 60,
        second=0,
        microsecond=0,
    ).astimezone(timezone.utc)


def _calendar_bucket(
    timestamp: datetime,
    interval: ResearchInterval,
) -> datetime:
    """Find the start of a daily, weekly, monthly, or quarterly period."""
    # Daily provider bars use a UTC-midnight date convention.
    trading_date = timestamp.astimezone(timezone.utc).date()

    if interval == ResearchInterval.WEEKLY:
        trading_date -= timedelta(days=trading_date.weekday())

    elif interval == ResearchInterval.MONTHLY:
        trading_date = trading_date.replace(day=1)

    elif interval == ResearchInterval.QUARTERLY:
        first_month = ((trading_date.month - 1) // 3) * 3 + 1
        trading_date = trading_date.replace(
            month=first_month,
            day=1,
        )

    return datetime(
        trading_date.year,
        trading_date.month,
        trading_date.day,
        tzinfo=timezone.utc,
    )


def aggregate_candles(
    candles: list[CandleData],
    interval: ResearchInterval,
    source_interval: ResearchInterval,
) -> list[AggregatedCandle]:
    """
    Aggregate source candles into the requested research interval.

    Minute intervals require one-minute source candles.
    Calendar intervals require daily source candles.

    The output contains one candle per populated interval.
    Empty periods are not fabricated.
    """
    if not candles:
        return []

    if interval in MINUTE_INTERVALS:
        if source_interval != ResearchInterval.ONE_MINUTE:
            raise ValueError("Intraday aggregation requires 1-minute candles.")

        expected_count = MINUTE_INTERVALS[interval]

    elif interval in (
        ResearchInterval.DAILY,
        ResearchInterval.WEEKLY,
        ResearchInterval.MONTHLY,
        ResearchInterval.QUARTERLY,
    ):
        if source_interval != ResearchInterval.DAILY:
            raise ValueError("Calendar aggregation requires daily candles.")

        expected_count = None

    else:
        raise ValueError("Unsupported research interval.")

    _validate_candles(candles)

    ordered = sorted(
        candles,
        key=lambda candle: candle.timestamp,
    )

    buckets = {}

    for candle in ordered:
        if interval in MINUTE_INTERVALS:
            bucket = _minute_bucket(
                candle.timestamp,
                MINUTE_INTERVALS[interval],
            )
        else:
            bucket = _calendar_bucket(candle.timestamp, interval)

        buckets.setdefault(bucket, []).append(candle)

    results = []

    for bucket_start, group in sorted(buckets.items()):
        aggregated = CandleData(
            timestamp=bucket_start,
            open_price=group[0].open_price,
            high_price=max(c.high_price for c in group),
            low_price=min(c.low_price for c in group),
            close_price=group[-1].close_price,
            volume=sum(c.volume for c in group),
        )

        results.append(
            AggregatedCandle(
                candle=aggregated,
                source_count=len(group),
                expected_count=expected_count,
            )
        )

    return results
