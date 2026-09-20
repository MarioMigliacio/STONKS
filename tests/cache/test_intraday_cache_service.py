# =============================================================================
# File: test_intraday_cache_service.py
# Purpose: Tests cache-aware intraday market-data retrieval.
# =============================================================================

from datetime import date, datetime, timezone
from unittest.mock import patch

from stonks.cache.intraday_cache_service import (
    _build_cache_data,
    _build_cache_file,
    _parse_cached_data,
    get_intraday_data,
)
from stonks.models.candle_data import CandleData
from stonks.models.timeframe import Timeframe


def build_candle_data() -> list[CandleData]:
    """Build reusable CandleData for cache service tests."""

    return [
        CandleData(
            timestamp=datetime(
                2026,
                9,
                16,
                8,
                0,
                tzinfo=timezone.utc,
            ),
            open_price=331.79,
            high_price=331.82,
            low_price=330.91,
            close_price=330.93,
            volume=37_224,
        ),
        CandleData(
            timestamp=datetime(
                2026,
                9,
                16,
                8,
                5,
                tzinfo=timezone.utc,
            ),
            open_price=330.92,
            high_price=331.68,
            low_price=330.92,
            close_price=330.96,
            volume=2_223,
        ),
    ]


@patch("stonks.cache.intraday_cache_service.USE_CACHE", True)
@patch("stonks.cache.intraday_cache_service.read_json")
@patch("stonks.cache.intraday_cache_service.get_aggregate_bars")
def test_get_intraday_data_returns_cached_data(
    mock_get_aggregate_bars,
    mock_read_json,
):
    """Verify cached intraday data is used without calling Massive."""

    candles = build_candle_data()

    mock_read_json.return_value = _build_cache_data(
        "AAPL",
        Timeframe.FIVE_MINUTES,
        date(2026, 9, 16),
        date(2026, 9, 16),
        candles,
    )

    result = get_intraday_data(
        "aapl",
        Timeframe.FIVE_MINUTES,
        date(2026, 9, 16),
        date(2026, 9, 16),
    )

    assert result == candles
    mock_get_aggregate_bars.assert_not_called()


@patch("stonks.cache.intraday_cache_service.USE_CACHE", True)
@patch("stonks.cache.intraday_cache_service.ALLOW_API_CALLS", True)
@patch("stonks.cache.intraday_cache_service.write_json")
@patch("stonks.cache.intraday_cache_service.read_json")
@patch("stonks.cache.intraday_cache_service.get_aggregate_bars")
def test_get_intraday_data_fetches_when_cache_missing(
    mock_get_aggregate_bars,
    mock_read_json,
    mock_write_json,
):
    """Verify missing intraday cache data is fetched and cached."""

    candles = build_candle_data()

    mock_read_json.return_value = None
    mock_get_aggregate_bars.return_value = candles

    result = get_intraday_data(
        "aapl",
        Timeframe.FIVE_MINUTES,
        date(2026, 9, 16),
        date(2026, 9, 16),
    )

    assert result == candles

    mock_get_aggregate_bars.assert_called_once_with(
        "AAPL",
        Timeframe.FIVE_MINUTES,
        date(2026, 9, 16),
        date(2026, 9, 16),
    )
    mock_write_json.assert_called_once()


@patch("stonks.cache.intraday_cache_service.USE_CACHE", True)
@patch("stonks.cache.intraday_cache_service.ALLOW_API_CALLS", False)
@patch("stonks.cache.intraday_cache_service.read_json")
@patch("stonks.cache.intraday_cache_service.get_aggregate_bars")
def test_get_intraday_data_returns_empty_when_api_calls_disabled(
    mock_get_aggregate_bars,
    mock_read_json,
):
    """Verify missing cache data returns empty when API calls are disabled."""

    mock_read_json.return_value = None

    result = get_intraday_data(
        "AAPL",
        Timeframe.FIVE_MINUTES,
        date(2026, 9, 16),
        date(2026, 9, 16),
    )

    assert result == []
    mock_get_aggregate_bars.assert_not_called()


@patch("stonks.cache.intraday_cache_service.USE_CACHE", True)
@patch("stonks.cache.intraday_cache_service.ALLOW_API_CALLS", True)
@patch("stonks.cache.intraday_cache_service.write_json")
@patch("stonks.cache.intraday_cache_service.read_json")
@patch("stonks.cache.intraday_cache_service.get_aggregate_bars")
def test_get_intraday_data_does_not_cache_failed_request(
    mock_get_aggregate_bars,
    mock_read_json,
    mock_write_json,
):
    """Verify unsuccessful Massive retrievals are not written to cache."""

    mock_read_json.return_value = None
    mock_get_aggregate_bars.return_value = []

    result = get_intraday_data(
        "AAPL",
        Timeframe.FIVE_MINUTES,
        date(2026, 9, 16),
        date(2026, 9, 16),
    )

    assert result == []
    mock_write_json.assert_not_called()


@patch("stonks.cache.intraday_cache_service.USE_CACHE", True)
@patch("stonks.cache.intraday_cache_service.ALLOW_API_CALLS", True)
@patch("stonks.cache.intraday_cache_service.write_json")
@patch("stonks.cache.intraday_cache_service.read_json")
@patch("stonks.cache.intraday_cache_service.get_aggregate_bars")
def test_get_intraday_data_force_refresh_bypasses_cache(
    mock_get_aggregate_bars,
    mock_read_json,
    mock_write_json,
):
    """Verify force refresh bypasses cached intraday data."""

    candles = build_candle_data()
    mock_get_aggregate_bars.return_value = candles

    result = get_intraday_data(
        "aapl",
        Timeframe.FIVE_MINUTES,
        date(2026, 9, 16),
        date(2026, 9, 16),
        force_refresh=True,
    )

    assert result == candles

    mock_read_json.assert_not_called()
    mock_get_aggregate_bars.assert_called_once_with(
        "AAPL",
        Timeframe.FIVE_MINUTES,
        date(2026, 9, 16),
        date(2026, 9, 16),
    )
    mock_write_json.assert_called_once()


def test_build_and_parse_cache_data_round_trip():
    """Verify CandleData survives cache serialization and deserialization."""

    candles = build_candle_data()

    cached_data = _build_cache_data(
        "AAPL",
        Timeframe.FIVE_MINUTES,
        date(2026, 9, 16),
        date(2026, 9, 16),
        candles,
    )

    parsed_data = _parse_cached_data(cached_data)

    assert parsed_data == candles
    assert cached_data["symbol"] == "AAPL"
    assert cached_data["timeframe"] == "5min"
    assert cached_data["start_date"] == "2026-09-16"
    assert cached_data["end_date"] == "2026-09-16"


def test_build_cache_file_contains_request_identity():
    """Verify cache filenames identify the symbol, timeframe, and date range."""

    cache_file = _build_cache_file(
        "AAPL",
        Timeframe.FIVE_MINUTES,
        date(2026, 9, 16),
        date(2026, 9, 16),
    )

    assert cache_file.name == "AAPL_5min_2026-09-16_2026-09-16.json"
