# =============================================================================
# File: price_action.py
# Purpose: Price-action functions calculate metrics from the candles supplied.
# =============================================================================

from typing import Optional

from stonks.models.candle_data import CandleData
from stonks.models.price_action_data import PriceActionData


def calculate_period_change(candles: list[CandleData]) -> Optional[float]:
    """Calculate percentage price change across the supplied candles."""

    if not candles:
        return None

    first_price = candles[0].open_price
    last_price = candles[-1].close_price

    if first_price == 0:
        return None

    return ((last_price - first_price) / first_price) * 100


def calculate_period_high(candles: list[CandleData]) -> Optional[float]:
    """Calculate the highest price across the supplied candles."""

    if not candles:
        return None

    return max(candle.high_price for candle in candles)


def calculate_period_low(
    candles: list[CandleData],
) -> Optional[float]:
    """Calculate the lowest price across the supplied candles."""

    if not candles:
        return None

    return min(candle.low_price for candle in candles)


def calculate_period_range(
    candles: list[CandleData],
) -> Optional[float]:
    """Calculate the range from the min and max across the supplied candles."""

    period_high = calculate_period_high(candles)
    period_low = calculate_period_low(candles)

    if period_high is None or period_low is None:
        return None

    if period_low == 0:
        return None

    return ((period_high - period_low) / period_low) * 100


def build_price_action_data(
    candles: list[CandleData],
) -> PriceActionData:
    """Build calculated price-action data from the supplied candles."""

    return PriceActionData(
        change_percent=calculate_period_change(candles),
        high_price=calculate_period_high(candles),
        low_price=calculate_period_low(candles),
        range_percent=calculate_period_range(candles),
    )
