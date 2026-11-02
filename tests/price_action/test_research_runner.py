# =============================================================================
# File: test_research_runner.py
# Purpose: Tests unified historical research retrieval and result construction.
# =============================================================================

from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from stonks.models.candle_data import CandleData
from stonks.models.historical_research_request import HistoricalResearchRequest
from stonks.models.historical_research_result import (
    ResearchDataSource,
    ResearchDataStatus,
)
from stonks.models.research_data_retrieval import (
    ResearchDataRetrieval,
    ResearchRetrievalStatus,
)
from stonks.models.research_interval import ResearchInterval
from stonks.models.timeframe import Timeframe
from stonks.price_action.research_runner import run_historical_research

MODULE = "stonks.price_action.research_runner"
TRADING_DATE = date(2026, 9, 28)


def make_request(interval, force_refresh=False, **kwargs):
    """Create a validated research request."""
    return HistoricalResearchRequest(
        symbol="aapl",
        start_date=TRADING_DATE,
        end_date=TRADING_DATE,
        interval=interval,
        force_refresh=force_refresh,
        **kwargs,
    )


def make_candles(count=5, daily=False):
    """Create chronologically ordered source candles."""
    start = datetime(
        2026,
        9,
        28,
        0 if daily else 13,
        0 if daily else 30,
        tzinfo=timezone.utc,
    )

    return [
        CandleData(
            timestamp=start
            + timedelta(
                days=index if daily else 0,
                minutes=0 if daily else index,
            ),
            open_price=100.0 + index,
            high_price=105.0 + index,
            low_price=99.0 + index,
            close_price=103.0 + index,
            volume=1000,
        )
        for index in range(count)
    ]


def successful_retrieval(candles, source):
    """Create a successful retrieval outcome."""
    return ResearchDataRetrieval(
        candles=candles,
        status=ResearchRetrievalStatus.SUCCESS,
        source=source,
    )


@patch(f"{MODULE}.retrieve_daily_research_data")
@patch(f"{MODULE}.retrieve_intraday_data")
def test_intraday_routes_to_one_minute_source(mock_intraday, mock_daily):
    """A five-minute chart must use one-minute source candles."""
    mock_intraday.return_value = successful_retrieval(
        make_candles(),
        ResearchDataSource.CACHE,
    )

    result = run_historical_research(make_request(ResearchInterval.FIVE_MINUTES))

    assert result.status == ResearchDataStatus.AVAILABLE
    assert result.data_source == ResearchDataSource.CACHE
    assert len(result.source_candles) == 5
    assert len(result.display_candles) == 1
    assert result.display_candles[0].volume == 5000

    assert mock_intraday.call_args.kwargs["timeframe"] == Timeframe.ONE_MINUTE
    mock_daily.assert_not_called()


@patch(f"{MODULE}.retrieve_daily_research_data")
@patch(f"{MODULE}.retrieve_intraday_data")
def test_daily_routes_to_daily_source(mock_intraday, mock_daily):
    """Calendar intervals must use daily source candles."""
    mock_daily.return_value = successful_retrieval(
        make_candles(count=1, daily=True),
        ResearchDataSource.PROVIDER,
    )

    result = run_historical_research(make_request(ResearchInterval.WEEKLY, force_refresh=True))

    assert result.status == ResearchDataStatus.AVAILABLE
    assert result.data_source == ResearchDataSource.PROVIDER
    assert len(result.display_candles) == 1
    assert mock_daily.call_args.kwargs["force_refresh"] is True
    mock_intraday.assert_not_called()


@patch(f"{MODULE}.retrieve_intraday_data")
def test_window_metrics_use_source_candles(mock_intraday):
    """Analysis metrics must use source data, not display buckets."""
    candles = make_candles()
    mock_intraday.return_value = successful_retrieval(
        candles,
        ResearchDataSource.CACHE,
    )

    result = run_historical_research(
        make_request(
            ResearchInterval.FIVE_MINUTES,
            window_start=candles[1].timestamp,
            window_end=candles[3].timestamp,
        )
    )

    assert result.window_metrics is not None
    assert result.window_metrics.candle_count == 2
    assert result.window_metrics.volume == 2000


@pytest.mark.parametrize(
    ("retrieval_status", "expected_status"),
    [
        (ResearchRetrievalStatus.NO_DATA, ResearchDataStatus.UNAVAILABLE),
        (ResearchRetrievalStatus.API_DISABLED, ResearchDataStatus.ERROR),
        (ResearchRetrievalStatus.PROVIDER_ERROR, ResearchDataStatus.ERROR),
        (ResearchRetrievalStatus.CACHE_ERROR, ResearchDataStatus.ERROR),
    ],
)
@patch(f"{MODULE}.retrieve_intraday_data")
def test_unsuccessful_retrieval_status(
    mock_intraday,
    retrieval_status,
    expected_status,
):
    """Retrieval failures must map to meaningful research statuses."""
    mock_intraday.return_value = ResearchDataRetrieval(
        candles=[],
        status=retrieval_status,
        message="Retrieval unavailable",
    )

    result = run_historical_research(make_request(ResearchInterval.ONE_MINUTE))

    assert result.status == expected_status
    assert result.source_candles == []
    assert result.display_candles == []
    assert result.window_metrics is None
    assert result.message == "Retrieval unavailable"


@patch(f"{MODULE}.retrieve_intraday_data")
def test_partial_aggregation_is_preserved(mock_intraday):
    """Missing source minutes should remain visible in final status."""
    candles = make_candles()
    candles.pop(2)

    mock_intraday.return_value = successful_retrieval(
        candles,
        ResearchDataSource.PROVIDER,
    )

    result = run_historical_research(make_request(ResearchInterval.FIVE_MINUTES))

    assert result.status == ResearchDataStatus.PARTIAL
    assert result.incomplete_display_periods == 1


@pytest.mark.parametrize(
    "interval",
    [
        ResearchInterval.ONE_MINUTE,
        ResearchInterval.FIVE_MINUTES,
        ResearchInterval.TEN_MINUTES,
        ResearchInterval.FIFTEEN_MINUTES,
        ResearchInterval.THIRTY_MINUTES,
        ResearchInterval.SIXTY_MINUTES,
    ],
)
@patch(f"{MODULE}.retrieve_daily_research_data")
@patch(f"{MODULE}.retrieve_intraday_data")
def test_all_intraday_intervals_use_one_minute_source(
    mock_intraday,
    mock_daily,
    interval,
):
    """All intraday chart intervals must retrieve one-minute data."""
    candles = make_candles(count=60)

    # Align the fixture to complete clock-hour aggregation buckets.
    for candle in candles:
        candle.timestamp += timedelta(minutes=30)

    mock_intraday.return_value = successful_retrieval(
        candles,
        ResearchDataSource.CACHE,
    )

    result = run_historical_research(make_request(interval, force_refresh=True))

    assert result.status == ResearchDataStatus.AVAILABLE
    assert len(result.source_candles) == 60
    assert len(result.display_candles) == (
        60
        // {
            ResearchInterval.ONE_MINUTE: 1,
            ResearchInterval.FIVE_MINUTES: 5,
            ResearchInterval.TEN_MINUTES: 10,
            ResearchInterval.FIFTEEN_MINUTES: 15,
            ResearchInterval.THIRTY_MINUTES: 30,
            ResearchInterval.SIXTY_MINUTES: 60,
        }[interval]
    )

    kwargs = mock_intraday.call_args.kwargs
    assert kwargs["symbol"] == "AAPL"
    assert kwargs["timeframe"] == Timeframe.ONE_MINUTE
    assert kwargs["force_refresh"] is True

    mock_daily.assert_not_called()


@pytest.mark.parametrize(
    "interval",
    [
        ResearchInterval.DAILY,
        ResearchInterval.WEEKLY,
        ResearchInterval.MONTHLY,
        ResearchInterval.QUARTERLY,
    ],
)
@patch(f"{MODULE}.retrieve_daily_research_data")
@patch(f"{MODULE}.retrieve_intraday_data")
def test_all_calendar_intervals_use_daily_source(
    mock_intraday,
    mock_daily,
    interval,
):
    """Calendar chart intervals must retrieve daily candles."""
    mock_daily.return_value = successful_retrieval(
        make_candles(count=1, daily=True),
        ResearchDataSource.PROVIDER,
    )

    result = run_historical_research(make_request(interval))

    assert result.status == ResearchDataStatus.AVAILABLE
    assert len(result.display_candles) == 1
    assert mock_daily.call_args.kwargs["symbol"] == "AAPL"
    mock_intraday.assert_not_called()
