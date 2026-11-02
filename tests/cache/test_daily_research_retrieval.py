# =============================================================================
# File: test_daily_research_retrieval.py
# Purpose: Tests daily research retrieval, cache reuse, and provider failures.
# =============================================================================

from datetime import date
from unittest.mock import patch

from stonks.cache.historical_cache_service import retrieve_daily_research_data
from stonks.models.historical_research_result import ResearchDataSource
from stonks.models.research_data_retrieval import ResearchRetrievalStatus

START = date(2026, 9, 28)
END = date(2026, 9, 29)

MODULE = "stonks.cache.historical_cache_service"


def make_daily_response():
    """Create a valid Alpha Vantage daily time-series response."""
    return {
        "Time Series (Daily)": {
            "2026-09-28": {
                "1. open": "100.00",
                "2. high": "105.00",
                "3. low": "99.00",
                "4. close": "103.00",
                "5. volume": "1000",
            }
        }
    }


def retrieve(force_refresh=False):
    """Retrieve the standard test date range."""
    return retrieve_daily_research_data(
        "aapl",
        START,
        END,
        force_refresh=force_refresh,
    )


@patch(f"{MODULE}.USE_CACHE", True)
@patch(f"{MODULE}.read_json")
@patch(f"{MODULE}.get_daily_time_series")
def test_cache_hit_skips_provider(mock_provider, mock_read):
    """Cached daily candles should avoid an API request."""
    mock_read.return_value = make_daily_response()

    result = retrieve()

    assert result.status == ResearchRetrievalStatus.SUCCESS
    assert result.source == ResearchDataSource.CACHE
    assert len(result.candles) == 1
    mock_provider.assert_not_called()


@patch(f"{MODULE}.USE_CACHE", True)
@patch(f"{MODULE}.ALLOW_API_CALLS", True)
@patch(f"{MODULE}.write_json")
@patch(f"{MODULE}.read_json", return_value=None)
@patch(f"{MODULE}.get_daily_time_series")
def test_provider_success(mock_provider, mock_read, mock_write):
    """Provider candles should be normalized and cached."""
    mock_provider.return_value = make_daily_response()

    result = retrieve()

    assert result.status == ResearchRetrievalStatus.SUCCESS
    assert result.source == ResearchDataSource.PROVIDER
    assert result.candles[0].close_price == 103.0
    assert mock_provider.call_args.kwargs["raise_on_error"] is True
    mock_write.assert_called_once()


@patch(f"{MODULE}.USE_CACHE", True)
@patch(f"{MODULE}.ALLOW_API_CALLS", True)
@patch(f"{MODULE}.write_json")
@patch(f"{MODULE}.read_json")
@patch(f"{MODULE}.get_daily_time_series")
def test_refresh_bypasses_cache(mock_provider, mock_read, mock_write):
    """Explicit refresh must fetch fresh provider data."""
    mock_provider.return_value = make_daily_response()

    result = retrieve(force_refresh=True)

    assert result.source == ResearchDataSource.PROVIDER
    mock_read.assert_not_called()
    mock_provider.assert_called_once()


@patch(f"{MODULE}.USE_CACHE", True)
@patch(f"{MODULE}.ALLOW_API_CALLS", True)
@patch(f"{MODULE}.read_json")
@patch(f"{MODULE}.get_daily_time_series")
def test_failed_refresh_does_not_use_stale_cache(mock_provider, mock_read):
    """Failed refresh must not return old cached candles."""
    mock_provider.side_effect = RuntimeError("Rate limited")

    result = retrieve(force_refresh=True)

    assert result.status == ResearchRetrievalStatus.PROVIDER_ERROR
    assert result.candles == []
    mock_read.assert_not_called()


@patch(f"{MODULE}.USE_CACHE", True)
@patch(f"{MODULE}.ALLOW_API_CALLS", False)
@patch(f"{MODULE}.read_json", return_value=None)
@patch(f"{MODULE}.get_daily_time_series")
def test_api_disabled(mock_provider, mock_read):
    """Disabled API access should not call the provider."""
    result = retrieve()

    assert result.status == ResearchRetrievalStatus.API_DISABLED
    assert result.source is None
    mock_provider.assert_not_called()


@patch(f"{MODULE}.USE_CACHE", False)
@patch(f"{MODULE}.ALLOW_API_CALLS", True)
@patch(f"{MODULE}.get_daily_time_series")
def test_valid_empty_series(mock_provider):
    """An empty daily series is a no-data outcome."""
    mock_provider.return_value = {"Time Series (Daily)": {}}

    result = retrieve()

    assert result.status == ResearchRetrievalStatus.NO_DATA
    assert result.source == ResearchDataSource.PROVIDER


@patch(f"{MODULE}.USE_CACHE", True)
@patch(f"{MODULE}.ALLOW_API_CALLS", True)
@patch(f"{MODULE}.write_json")
@patch(f"{MODULE}.read_json")
@patch(f"{MODULE}.get_daily_time_series")
def test_corrupt_cache_refetches(mock_provider, mock_read, mock_write):
    """Malformed cached responses should trigger a fresh retrieval."""
    mock_read.return_value = {"Information": "Rate limit exceeded"}
    mock_provider.return_value = make_daily_response()

    result = retrieve()

    assert result.status == ResearchRetrievalStatus.SUCCESS
    assert result.source == ResearchDataSource.PROVIDER
    mock_provider.assert_called_once()


@patch(f"{MODULE}.USE_CACHE", True)
@patch(f"{MODULE}.ALLOW_API_CALLS", False)
@patch(f"{MODULE}.read_json")
@patch(f"{MODULE}.get_daily_time_series")
def test_corrupt_cache_without_api(mock_provider, mock_read):
    """Invalid cache should never be presented as valid candles."""
    mock_read.return_value = {"Information": "Rate limit exceeded"}

    result = retrieve()

    assert result.status == ResearchRetrievalStatus.CACHE_ERROR
    assert "cache" in result.message.lower()
    mock_provider.assert_not_called()


@patch(f"{MODULE}.USE_CACHE", False)
@patch(f"{MODULE}.ALLOW_API_CALLS", True)
@patch(f"{MODULE}.get_daily_time_series")
def test_malformed_provider_candles(mock_provider):
    """Invalid OHLCV data must be rejected."""
    data = make_daily_response()
    data["Time Series (Daily)"]["2026-09-28"]["2. high"] = "50.00"
    mock_provider.return_value = data

    result = retrieve()

    assert result.status == ResearchRetrievalStatus.PROVIDER_ERROR
    assert result.candles == []
