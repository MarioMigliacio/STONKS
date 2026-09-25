# =============================================================================
# File: candle_selection.py
# Purpose:
# =============================================================================

from datetime import time

from stonks.config.market_hours import (
    AFTER_HOURS_CLOSE,
    MARKET_TIMEZONE,
    PRE_MARKET_OPEN,
    REGULAR_MARKET_CLOSE,
    REGULAR_MARKET_OPEN,
)
from stonks.models.candle_data import CandleData
from stonks.models.market_session import MarketSession


def get_session_candles(
    candles: list[CandleData],
    session: MarketSession,
) -> list[CandleData]:
    """Return candles belonging to the requested market session."""

    session_start, session_end = _get_session_bounds(session)

    selected_candles: list[CandleData] = []

    for candle in candles:
        market_time = candle.timestamp.astimezone(MARKET_TIMEZONE).time()

        if session_start <= market_time < session_end:
            selected_candles.append(candle)

    return selected_candles


def _get_session_bounds(
    session: MarketSession,
) -> tuple[time, time]:
    """Return the start and end times for a market session."""

    if session == MarketSession.PRE_MARKET:
        return PRE_MARKET_OPEN, REGULAR_MARKET_OPEN

    if session == MarketSession.REGULAR:
        return REGULAR_MARKET_OPEN, REGULAR_MARKET_CLOSE

    if session == MarketSession.AFTER_HOURS:
        return REGULAR_MARKET_CLOSE, AFTER_HOURS_CLOSE

    raise ValueError(f"Unsupported market session: {session}")
