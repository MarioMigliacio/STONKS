# =============================================================================
# File: candle_window.py
# Purpose: Selects historical candles within a specified time window.
# =============================================================================

from datetime import datetime

from stonks.models.candle_data import CandleData


def select_candle_window(
    candles: list[CandleData],
    start_time: datetime,
    end_time: datetime,
) -> list[CandleData]:
    """
    Select candles whose timestamps fall within a time window.

    The interval includes start_time and excludes end_time.
    All timestamps must be timezone-aware.

    Args:
        candles:
            Source candles to filter.

        start_time:
            Inclusive window start.

        end_time:
            Exclusive window end.

    Returns:
        Selected candles ordered chronologically.

    Raises:
        ValueError:
            If timestamps are invalid or timezone-naive.
    """
    if start_time.tzinfo is None or start_time.utcoffset() is None:
        raise ValueError("Window start must be timezone-aware.")

    if end_time.tzinfo is None or end_time.utcoffset() is None:
        raise ValueError("Window end must be timezone-aware.")

    if start_time >= end_time:
        raise ValueError("Window start must precede window end.")

    for candle in candles:
        if candle.timestamp.tzinfo is None or candle.timestamp.utcoffset() is None:
            raise ValueError("Candle timestamps must be timezone-aware.")

    selected = [candle for candle in candles if start_time <= candle.timestamp < end_time]

    return sorted(selected, key=lambda candle: candle.timestamp)
