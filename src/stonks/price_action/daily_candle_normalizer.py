# =============================================================================
# File: daily_candle_normalizer.py
# Purpose: Normalizes Alpha Vantage daily OHLCV data into CandleData.
# =============================================================================

from datetime import date, datetime, timezone

from stonks.models.candle_data import CandleData


def normalize_daily_candles(
    data: dict,
    start_date: date,
    end_date: date,
) -> list[CandleData]:
    """
    Normalize daily historical data for a requested date range.

    Args:
        data:
            Alpha Vantage daily time-series response.

        start_date:
            First requested trading date, inclusive.

        end_date:
            Last requested trading date, inclusive.

    Returns:
        Chronologically ordered daily CandleData objects.

    Raises:
        ValueError:
            If the response is invalid or contains malformed candles.
    """
    if start_date > end_date:
        raise ValueError("Start date must not exceed end date.")

    series = data.get("Time Series (Daily)")

    if not isinstance(series, dict):
        raise ValueError("Daily time-series data is unavailable or invalid.")

    candles = []

    for date_text, values in series.items():
        trading_date = date.fromisoformat(date_text)

        if not start_date <= trading_date <= end_date:
            continue

        candle = CandleData(
            timestamp=datetime(
                trading_date.year,
                trading_date.month,
                trading_date.day,
                tzinfo=timezone.utc,
            ),
            open_price=float(values["1. open"]),
            high_price=float(values["2. high"]),
            low_price=float(values["3. low"]),
            close_price=float(values["4. close"]),
            volume=int(values["5. volume"]),
        )

        if (
            candle.low_price <= 0
            or candle.high_price < candle.low_price
            or candle.high_price < max(candle.open_price, candle.close_price)
            or candle.low_price > min(candle.open_price, candle.close_price)
            or candle.volume < 0
        ):
            raise ValueError(f"Invalid daily OHLCV values for {date_text}.")

        candles.append(candle)

    return sorted(candles, key=lambda candle: candle.timestamp)
