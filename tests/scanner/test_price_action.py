# =============================================================================
# File: test_price_action.py
# Purpose: Tests price-action calculations across supplied candle data.
# =============================================================================

from datetime import datetime, timezone

import pytest

from stonks.models.candle_data import CandleData
from stonks.scanner.price_action import (
    calculate_period_change,
    calculate_period_high,
    calculate_period_low,
    calculate_period_range,
)


def build_candles() -> list[CandleData]:
    """Build reusable candle data for price-action tests."""

    return [
        CandleData(
            timestamp=datetime(
                2026,
                9,
                16,
                13,
                30,
                tzinfo=timezone.utc,
            ),
            open_price=10.00,
            high_price=10.75,
            low_price=9.50,
            close_price=10.50,
            volume=100_000,
        ),
        CandleData(
            timestamp=datetime(
                2026,
                9,
                16,
                13,
                35,
                tzinfo=timezone.utc,
            ),
            open_price=10.50,
            high_price=12.00,
            low_price=10.25,
            close_price=11.50,
            volume=150_000,
        ),
        CandleData(
            timestamp=datetime(
                2026,
                9,
                16,
                13,
                40,
                tzinfo=timezone.utc,
            ),
            open_price=11.50,
            high_price=11.75,
            low_price=10.75,
            close_price=11.00,
            volume=125_000,
        ),
    ]


def test_calculate_period_change_returns_positive_change():
    """Verify period change uses the first open and last close."""

    candles = build_candles()

    result = calculate_period_change(candles)

    assert result == pytest.approx(10.0)


def test_calculate_period_change_returns_negative_change():
    """Verify downward price movement produces a negative percentage."""

    candles = build_candles()
    candles[-1].close_price = 9.00

    result = calculate_period_change(candles)

    assert result == pytest.approx(-10.0)


def test_calculate_period_change_returns_none_for_empty_candles():
    """Verify period change is unavailable without candle data."""

    assert calculate_period_change([]) is None


def test_calculate_period_change_returns_none_for_zero_open_price():
    """Verify a zero starting price does not cause division by zero."""

    candles = build_candles()
    candles[0].open_price = 0.0

    assert calculate_period_change(candles) is None


def test_calculate_period_high_returns_highest_candle_high():
    """Verify period high uses candle high prices."""

    candles = build_candles()

    result = calculate_period_high(candles)

    assert result == pytest.approx(12.00)


def test_calculate_period_high_returns_none_for_empty_candles():
    """Verify period high is unavailable without candle data."""

    assert calculate_period_high([]) is None


def test_calculate_period_low_returns_lowest_candle_low():
    """Verify period low uses candle low prices."""

    candles = build_candles()

    result = calculate_period_low(candles)

    assert result == pytest.approx(9.50)


def test_calculate_period_low_returns_none_for_empty_candles():
    """Verify period low is unavailable without candle data."""

    assert calculate_period_low([]) is None


def test_calculate_period_range_returns_percentage_range():
    """Verify period range is measured relative to the period low."""

    candles = build_candles()

    result = calculate_period_range(candles)

    expected = ((12.00 - 9.50) / 9.50) * 100

    assert result == pytest.approx(expected)


def test_calculate_period_range_returns_none_for_empty_candles():
    """Verify period range is unavailable without candle data."""

    assert calculate_period_range([]) is None


def test_calculate_period_range_returns_none_for_zero_period_low():
    """Verify a zero period low does not cause division by zero."""

    candles = build_candles()
    candles[0].low_price = 0.0

    assert calculate_period_range(candles) is None
