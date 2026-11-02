# =============================================================================
# File: test_intraday_research_retrieval.py
# Purpose: Tests cache-aware intraday research retrieval outcomes.
# =============================================================================

from datetime import date, datetime, timezone
from unittest.mock import patch

from stonks.cache.intraday_cache_service import (
    _build_cache_data,
    retrieve_intraday_data,
)
from stonks.models.candle_data import CandleData
from stonks.models.historical_research_result import ResearchDataSource
from stonks.models.research_data_retrieval import ResearchRetrievalStatus
from stonks.models.timeframe import Timeframe

START_DATE = date(2026, 9, 28)
END_DATE = date(2026, 9, 28)


def make_candle() -> CandleData:
    """Create a normalized one-minute candle."""
    return CandleData(
        timestamp=datetime(2026, 9, 28, 13, 30, tzinfo=timezone.utc),
        open_price=100.0,
        high_price=105.0,
        low_price=99.0,
        close_price=103.0,
        volume=1000,
    )


def retrieve(force_refresh: bool = False):
    """Execute the standard test retrieval request."""
    return retrieve_intraday_data(
        "aapl",
        Timeframe.ONE_MINUTE,
        START_DATE,
        END_DATE,
        force_refresh=force_refresh,
    )


@patch("stonks.cache.intraday_cache_service.USE_CACHE", True)
@patch("stonks.cache.intraday_cache_service.read_json")
@patch("stonks.cache.intraday_cache_service.get_aggregate_bars")
def test_cache_hit_skips_provider(mock_provider, mock_read) -> None:
    """Cached candles should not consume provider requests."""
    mock_read.return_value = _build_cache_data(
        "AAPL",
        Timeframe.ONE_MINUTE,
        START_DATE,
        END_DATE,
        [make_candle()],
    )

    result = retrieve()

    assert result.status == ResearchRetrievalStatus.SUCCESS
    assert result.source == ResearchDataSource.CACHE
    assert len(result.candles) == 1
    mock_provider.assert_not_called()


@patch("stonks.cache.intraday_cache_service.USE_CACHE", True)
@patch("stonks.cache.intraday_cache_service.ALLOW_API_CALLS", True)
@patch("stonks.cache.intraday_cache_service.write_json")
@patch("stonks.cache.intraday_cache_service.read_json", return_value=None)
@patch("stonks.cache.intraday_cache_service.get_aggregate_bars")
def test_provider_success(mock_provider, mock_read, mock_write) -> None:
    """Provider data should be returned and cached."""
    mock_provider.return_value = [make_candle()]

    result = retrieve()

    assert result.status == ResearchRetrievalStatus.SUCCESS
    assert result.source == ResearchDataSource.PROVIDER
    assert len(result.candles) == 1
    assert mock_provider.call_args.kwargs["raise_on_error"] is True
    mock_write.assert_called_once()


@patch("stonks.cache.intraday_cache_service.USE_CACHE", True)
@patch("stonks.cache.intraday_cache_service.ALLOW_API_CALLS", True)
@patch("stonks.cache.intraday_cache_service.write_json")
@patch("stonks.cache.intraday_cache_service.read_json")
@patch("stonks.cache.intraday_cache_service.get_aggregate_bars")
def test_refresh_bypasses_cache(
    mock_provider,
    mock_read,
    mock_write,
) -> None:
    """Explicit refresh must bypass existing cached data."""
    mock_provider.return_value = [make_candle()]

    result = retrieve(force_refresh=True)

    assert result.source == ResearchDataSource.PROVIDER
    mock_read.assert_not_called()
    mock_provider.assert_called_once()


@patch("stonks.cache.intraday_cache_service.USE_CACHE", True)
@patch("stonks.cache.intraday_cache_service.ALLOW_API_CALLS", True)
@patch("stonks.cache.intraday_cache_service.read_json")
@patch("stonks.cache.intraday_cache_service.get_aggregate_bars")
def test_failed_refresh_does_not_use_stale_cache(
    mock_provider,
    mock_read,
) -> None:
    """Provider failure must not silently return cached candles."""
    mock_provider.side_effect = RuntimeError("Provider unavailable")

    result = retrieve(force_refresh=True)

    assert result.status == ResearchRetrievalStatus.PROVIDER_ERROR
    assert result.source == ResearchDataSource.PROVIDER
    assert result.candles == []
    mock_read.assert_not_called()


@patch("stonks.cache.intraday_cache_service.ALLOW_API_CALLS", False)
@patch("stonks.cache.intraday_cache_service.read_json", return_value=None)
@patch("stonks.cache.intraday_cache_service.get_aggregate_bars")
def test_api_disabled(mock_provider, mock_read) -> None:
    """Disabled API access should not invoke Massive."""
    result = retrieve()

    assert result.status == ResearchRetrievalStatus.API_DISABLED
    assert result.source is None
    mock_provider.assert_not_called()


@patch("stonks.cache.intraday_cache_service.USE_CACHE", True)
@patch("stonks.cache.intraday_cache_service.ALLOW_API_CALLS", True)
@patch("stonks.cache.intraday_cache_service.read_json", return_value=None)
@patch("stonks.cache.intraday_cache_service.get_aggregate_bars")
def test_provider_no_data(mock_provider, mock_read) -> None:
    """Valid empty provider responses must remain distinguishable."""
    mock_provider.return_value = []

    result = retrieve()

    assert result.status == ResearchRetrievalStatus.NO_DATA
    assert result.source == ResearchDataSource.PROVIDER
    assert result.candles == []


@patch("stonks.cache.intraday_cache_service.USE_CACHE", True)
@patch("stonks.cache.intraday_cache_service.ALLOW_API_CALLS", True)
@patch("stonks.cache.intraday_cache_service.read_json")
@patch("stonks.cache.intraday_cache_service.get_aggregate_bars")
def test_corrupt_cache_refetches(mock_provider, mock_read) -> None:
    """Malformed cache entries should be rejected and refetched."""
    mock_read.return_value = {
        "symbol": "AAPL",
        "timeframe": "1min",
        "start_date": START_DATE.isoformat(),
        "end_date": END_DATE.isoformat(),
        "candles": [{"timestamp": "not-a-date"}],
    }

    mock_provider.return_value = [make_candle()]

    with patch("stonks.cache.intraday_cache_service.write_json"):
        result = retrieve()

    assert result.status == ResearchRetrievalStatus.SUCCESS
    assert result.source == ResearchDataSource.PROVIDER
    mock_provider.assert_called_once()


@patch("stonks.cache.intraday_cache_service.USE_CACHE", True)
@patch("stonks.cache.intraday_cache_service.ALLOW_API_CALLS", False)
@patch("stonks.cache.intraday_cache_service.read_json")
@patch("stonks.cache.intraday_cache_service.get_aggregate_bars")
def test_corrupt_cache_without_api(mock_provider, mock_read) -> None:
    """Invalid local data must not be treated as valid research data."""
    mock_read.return_value = {"candles": "invalid"}

    result = retrieve()

    assert result.status == ResearchRetrievalStatus.CACHE_ERROR
    assert "cache" in result.message.lower()
    mock_provider.assert_not_called()
