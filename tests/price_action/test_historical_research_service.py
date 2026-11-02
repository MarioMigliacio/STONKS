# =============================================================================
# File: test_historical_research_service.py
# Purpose: Tests pure historical research orchestration.
# =============================================================================

from datetime import date, datetime, timedelta, timezone

import pytest

from stonks.models.candle_data import CandleData
from stonks.models.historical_research_request import HistoricalResearchRequest
from stonks.models.historical_research_result import (
    ResearchDataSource,
    ResearchDataStatus,
)
from stonks.models.market_session import MarketSession
from stonks.models.research_interval import ResearchInterval
from stonks.price_action.historical_research_service import (
    build_historical_research_result,
)


def make_candle(
    timestamp: datetime,
    open_price: float,
    close_price: float,
    high_price: float,
    low_price: float,
    volume: int = 100,
) -> CandleData:
    """Create a normalized test candle."""
    return CandleData(
        timestamp=timestamp,
        open_price=open_price,
        high_price=high_price,
        low_price=low_price,
        close_price=close_price,
        volume=volume,
    )


def test_aggregates_intraday_candles() -> None:
    """Five one-minute candles should form one five-minute candle."""
    start = datetime(2026, 9, 28, 13, 30, tzinfo=timezone.utc)

    candles = [
        make_candle(
            start + timedelta(minutes=index),
            100 + index,
            101 + index,
            102 + index,
            99 + index,
        )
        for index in range(5)
    ]

    request = HistoricalResearchRequest(
        symbol="aapl",
        start_date=date(2026, 9, 28),
        end_date=date(2026, 9, 28),
        interval=ResearchInterval.FIVE_MINUTES,
    )

    result = build_historical_research_result(
        request,
        candles,
        ResearchDataSource.CACHE,
    )

    assert result.status == ResearchDataStatus.AVAILABLE
    assert result.data_source == ResearchDataSource.CACHE
    assert len(result.source_candles) == 5
    assert len(result.display_candles) == 1
    assert result.display_candles[0].open_price == 100
    assert result.display_candles[0].close_price == 105
    assert result.display_candles[0].volume == 500
    assert result.window_metrics is None


def test_window_metrics_use_source_candles() -> None:
    """Window analysis must not depend on chart aggregation."""
    start = datetime(2026, 9, 28, 13, 30, tzinfo=timezone.utc)

    candles = [
        make_candle(
            start + timedelta(minutes=index),
            100 + index,
            101 + index,
            102 + index,
            99 + index,
        )
        for index in range(5)
    ]

    request = HistoricalResearchRequest(
        symbol="AAPL",
        start_date=date(2026, 9, 28),
        end_date=date(2026, 9, 28),
        interval=ResearchInterval.FIVE_MINUTES,
        window_start=start + timedelta(minutes=1),
        window_end=start + timedelta(minutes=4),
    )

    result = build_historical_research_result(request, candles)

    metrics = result.window_metrics

    assert metrics is not None
    assert metrics.candle_count == 3
    assert metrics.volume == 300
    assert metrics.price_action.high_price == 105
    assert metrics.price_action.low_price == 100
    assert metrics.price_action.change_percent == pytest.approx((104 - 101) / 101 * 100)


def test_filters_intraday_market_session() -> None:
    """Regular-session research must exclude premarket candles."""
    candles = [
        make_candle(
            datetime(2026, 9, 28, 12, 0, tzinfo=timezone.utc),
            90,
            91,
            92,
            89,
        ),
        make_candle(
            datetime(2026, 9, 28, 13, 30, tzinfo=timezone.utc),
            100,
            101,
            102,
            99,
        ),
    ]

    request = HistoricalResearchRequest(
        symbol="AAPL",
        start_date=date(2026, 9, 28),
        end_date=date(2026, 9, 28),
        interval=ResearchInterval.ONE_MINUTE,
        session=MarketSession.REGULAR,
    )

    result = build_historical_research_result(request, candles)

    assert len(result.source_candles) == 1
    assert result.source_candles[0].open_price == 100


def test_reports_missing_source_candles() -> None:
    """Incomplete five-minute buckets should be reported."""
    start = datetime(2026, 9, 28, 13, 30, tzinfo=timezone.utc)

    candles = [
        make_candle(
            start + timedelta(minutes=index),
            100,
            101,
            102,
            99,
        )
        for index in (0, 1, 3, 4)
    ]

    request = HistoricalResearchRequest(
        symbol="AAPL",
        start_date=date(2026, 9, 28),
        end_date=date(2026, 9, 28),
        interval=ResearchInterval.FIVE_MINUTES,
    )

    result = build_historical_research_result(request, candles)

    assert result.status == ResearchDataStatus.PARTIAL
    assert result.incomplete_display_periods == 1
    assert len(result.display_candles) == 1


def test_returns_unavailable_for_empty_data() -> None:
    """No matching candles should produce an unavailable result."""
    request = HistoricalResearchRequest(
        symbol="AAPL",
        start_date=date(2026, 9, 28),
        end_date=date(2026, 9, 28),
        interval=ResearchInterval.DAILY,
    )

    result = build_historical_research_result(request, [])

    assert result.status == ResearchDataStatus.UNAVAILABLE
    assert result.source_candles == []
    assert result.display_candles == []
    assert result.window_metrics is None


def test_aggregates_daily_candles_to_weekly() -> None:
    """Weekly research should aggregate normalized daily candles."""
    candles = [
        make_candle(
            datetime(2026, 9, 28, tzinfo=timezone.utc),
            100,
            102,
            103,
            99,
            1000,
        ),
        make_candle(
            datetime(2026, 9, 29, tzinfo=timezone.utc),
            102,
            105,
            106,
            101,
            2000,
        ),
    ]

    request = HistoricalResearchRequest(
        symbol="AAPL",
        start_date=date(2026, 9, 28),
        end_date=date(2026, 9, 29),
        interval=ResearchInterval.WEEKLY,
    )

    result = build_historical_research_result(request, candles)

    assert result.status == ResearchDataStatus.AVAILABLE
    assert len(result.display_candles) == 1
    assert result.display_candles[0].open_price == 100
    assert result.display_candles[0].close_price == 105
    assert result.display_candles[0].volume == 3000
