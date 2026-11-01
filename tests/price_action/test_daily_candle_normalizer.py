# =============================================================================
# File: test_daily_candle_normalizer.py
# Purpose: Tests normalization of daily historical OHLCV data.
# =============================================================================

from datetime import date, datetime, timezone

import pytest

from stonks.price_action.daily_candle_normalizer import normalize_daily_candles


def make_response() -> dict:
    """Create a representative Alpha Vantage daily response."""
    return {
        "Time Series (Daily)": {
            "2026-09-28": {
                "1. open": "110.00",
                "2. high": "115.00",
                "3. low": "108.00",
                "4. close": "112.00",
                "5. volume": "2000",
            },
            "2026-09-25": {
                "1. open": "100.00",
                "2. high": "105.00",
                "3. low": "98.00",
                "4. close": "103.00",
                "5. volume": "1000",
            },
        }
    }


def test_normalizes_and_sorts_daily_candles() -> None:
    """Daily data should become chronological CandleData."""
    candles = normalize_daily_candles(
        make_response(),
        date(2026, 9, 25),
        date(2026, 9, 28),
    )

    assert len(candles) == 2
    assert candles[0].timestamp == datetime(2026, 9, 25, tzinfo=timezone.utc)
    assert candles[0].open_price == 100.0
    assert candles[0].close_price == 103.0
    assert candles[0].volume == 1000
    assert candles[1].close_price == 112.0


def test_filters_requested_dates() -> None:
    """Exclude daily candles outside the requested date range."""
    candles = normalize_daily_candles(
        make_response(),
        date(2026, 9, 28),
        date(2026, 9, 28),
    )

    assert len(candles) == 1
    assert candles[0].close_price == 112.0


def test_rejects_missing_time_series() -> None:
    """API informational responses must not be treated as valid data."""
    with pytest.raises(ValueError):
        normalize_daily_candles(
            {"Information": "API limit reached"},
            date(2026, 9, 25),
            date(2026, 9, 28),
        )


def test_rejects_invalid_ohlcv() -> None:
    """Reject candles with impossible OHLCV relationships."""
    response = make_response()
    response["Time Series (Daily)"]["2026-09-25"]["2. high"] = "90.00"

    with pytest.raises(ValueError):
        normalize_daily_candles(
            response,
            date(2026, 9, 25),
            date(2026, 9, 28),
        )


def test_rejects_reversed_dates() -> None:
    """The requested date range must be valid."""
    with pytest.raises(ValueError):
        normalize_daily_candles(
            make_response(),
            date(2026, 9, 28),
            date(2026, 9, 25),
        )
