# =============================================================================
# File: test_candle_selection.py
# Purpose: Tests candle selection across U.S. market trading sessions.
# =============================================================================

from datetime import datetime, timezone

import pytest

from stonks.models.candle_data import CandleData
from stonks.models.market_session import MarketSession
from stonks.scanner.candle_selection import get_session_candles


def build_candle(
    timestamp: datetime,
) -> CandleData:
    """Build a candle with the supplied timestamp."""

    return CandleData(
        timestamp=timestamp,
        open_price=10.00,
        high_price=11.00,
        low_price=9.00,
        close_price=10.50,
        volume=100_000,
    )


def test_get_session_candles_selects_pre_market_candles():
    """Verify pre-market candles are selected from UTC timestamps."""

    candles = [
        build_candle(datetime(2026, 9, 16, 7, 59, 59, tzinfo=timezone.utc)),
        build_candle(datetime(2026, 9, 16, 8, 0, tzinfo=timezone.utc)),
        build_candle(datetime(2026, 9, 16, 13, 29, 59, tzinfo=timezone.utc)),
        build_candle(datetime(2026, 9, 16, 13, 30, tzinfo=timezone.utc)),
    ]

    result = get_session_candles(
        candles,
        MarketSession.PRE_MARKET,
    )

    assert result == candles[1:3]


def test_get_session_candles_selects_regular_session_candles():
    """Verify regular-session candles are selected from UTC timestamps."""

    candles = [
        build_candle(datetime(2026, 9, 16, 13, 29, 59, tzinfo=timezone.utc)),
        build_candle(datetime(2026, 9, 16, 13, 30, tzinfo=timezone.utc)),
        build_candle(datetime(2026, 9, 16, 19, 59, 59, tzinfo=timezone.utc)),
        build_candle(datetime(2026, 9, 16, 20, 0, tzinfo=timezone.utc)),
    ]

    result = get_session_candles(
        candles,
        MarketSession.REGULAR,
    )

    assert result == candles[1:3]


def test_get_session_candles_selects_after_hours_candles():
    """Verify after-hours candles are selected from UTC timestamps."""

    candles = [
        build_candle(datetime(2026, 9, 16, 19, 59, 59, tzinfo=timezone.utc)),
        build_candle(datetime(2026, 9, 16, 20, 0, tzinfo=timezone.utc)),
        build_candle(datetime(2026, 9, 16, 23, 59, 59, tzinfo=timezone.utc)),
        build_candle(datetime(2026, 9, 17, 0, 0, tzinfo=timezone.utc)),
    ]

    result = get_session_candles(
        candles,
        MarketSession.AFTER_HOURS,
    )

    assert result == candles[1:3]


def test_get_session_candles_returns_empty_for_no_matching_candles():
    """Verify an empty list is returned when no candles match."""

    candles = [
        build_candle(datetime(2026, 9, 16, 13, 30, tzinfo=timezone.utc)),
    ]

    result = get_session_candles(
        candles,
        MarketSession.PRE_MARKET,
    )

    assert result == []


def test_get_session_candles_returns_empty_for_empty_input():
    """Verify empty candle input produces an empty result."""

    result = get_session_candles(
        [],
        MarketSession.REGULAR,
    )

    assert result == []


def test_get_session_candles_preserves_candle_order():
    """Verify selected candles retain their original ordering."""

    candles = [
        build_candle(datetime(2026, 9, 16, 15, 30, tzinfo=timezone.utc)),
        build_candle(datetime(2026, 9, 16, 13, 30, tzinfo=timezone.utc)),
        build_candle(datetime(2026, 9, 16, 17, 30, tzinfo=timezone.utc)),
    ]

    result = get_session_candles(
        candles,
        MarketSession.REGULAR,
    )

    assert result == candles


def test_get_session_candles_preserves_utc_timestamp():
    """Verify session selection does not mutate candle timestamps."""

    candle = build_candle(datetime(2026, 9, 16, 13, 30, tzinfo=timezone.utc))

    result = get_session_candles(
        [candle],
        MarketSession.REGULAR,
    )

    assert result[0].timestamp == datetime(
        2026,
        9,
        16,
        13,
        30,
        tzinfo=timezone.utc,
    )


def test_get_session_candles_handles_standard_time():
    """Verify session selection handles Eastern Standard Time."""

    candle = build_candle(datetime(2026, 1, 15, 14, 30, tzinfo=timezone.utc))

    result = get_session_candles(
        [candle],
        MarketSession.REGULAR,
    )

    assert result == [candle]


def test_get_session_candles_handles_daylight_saving_time():
    """Verify session selection handles Eastern Daylight Time."""

    candle = build_candle(datetime(2026, 7, 15, 13, 30, tzinfo=timezone.utc))

    result = get_session_candles(
        [candle],
        MarketSession.REGULAR,
    )

    assert result == [candle]


def test_get_session_candles_rejects_unsupported_session():
    """Verify unsupported sessions fail explicitly."""

    candles = [
        build_candle(datetime(2026, 9, 16, 13, 30, tzinfo=timezone.utc)),
    ]

    with pytest.raises(ValueError):
        get_session_candles(
            candles,
            "unsupported",  # type: ignore[arg-type]
        )
