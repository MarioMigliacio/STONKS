# =============================================================================
# File: test_filters.py
# Purpose: Pytest file for scanner filter and integration behavior.
# =============================================================================

from datetime import date, datetime, timezone
from unittest.mock import patch

import pytest

from stonks.config.settings import PRICE_ACTION_LOOKBACKS
from stonks.models.candle_data import CandleData
from stonks.models.float_data import FloatData
from stonks.models.market_session import MarketSession
from stonks.models.timeframe import Timeframe
from stonks.scanner.filters import scan_stocks
from stonks.scanner.float_classification import FloatClassification


def build_quote_response(volume: int) -> dict:
    """Build reusable Alpha Vantage quote response data for scanner tests."""

    return {
        "Global Quote": {
            "01. symbol": "BIVI",
            "02. open": "2.00",
            "05. price": "2.50",
            "06. volume": str(volume),
            "07. latest trading day": "2026-09-08",
            "08. previous close": "1.80",
            "10. change percent": "38.89%",
        }
    }


def build_float_data() -> FloatData:
    """Build reusable FloatData for scanner tests."""

    return FloatData(
        symbol="BIVI",
        float_shares=7_500_000,
        float_percent=62.5,
        effective_date=date(2026, 8, 20),
        source="Massive",
    )


def build_candle(
    timestamp: datetime,
    open_price: float,
    high_price: float,
    low_price: float,
    close_price: float,
) -> CandleData:
    """Build reusable CandleData for scanner tests."""

    return CandleData(
        timestamp=timestamp,
        open_price=open_price,
        high_price=high_price,
        low_price=low_price,
        close_price=close_price,
        volume=100_000,
    )


@patch("stonks.scanner.filters.WATCHLIST", ["BIVI"])
@patch("stonks.scanner.filters.MIN_VOLUME", 1_000)
@patch("stonks.scanner.filters.time.sleep")
@patch("stonks.scanner.filters.classify_float_size")
@patch("stonks.scanner.filters.calculate_float_turnover")
@patch("stonks.scanner.filters.calculate_relative_volume")
@patch("stonks.scanner.filters.calculate_average_volume")
@patch("stonks.scanner.filters.parse_historical_volumes")
@patch("stonks.scanner.filters.get_historical_data")
@patch("stonks.scanner.filters.get_intraday_data")
@patch("stonks.scanner.filters.get_float_data")
@patch("stonks.scanner.filters.get_quote")
def test_scan_stocks_adds_float_data_to_candidate(
    mock_get_quote,
    mock_get_float_data,
    mock_get_intraday_data,
    mock_get_historical_data,
    mock_parse_historical_volumes,
    mock_calculate_average_volume,
    mock_calculate_relative_volume,
    mock_calculate_float_turnover,
    mock_classify_float_size,
    mock_sleep,
):
    """Verify a qualifying stock is returned with float scanner metrics."""

    float_data = build_float_data()

    mock_get_quote.return_value = build_quote_response(volume=5_000)
    mock_get_historical_data.return_value = {"historical": "data"}
    mock_parse_historical_volumes.return_value = []
    mock_calculate_average_volume.return_value = 2_500.0
    mock_calculate_relative_volume.return_value = 2.0
    mock_get_float_data.return_value = float_data
    mock_get_intraday_data.return_value = []
    mock_calculate_float_turnover.return_value = 0.25
    mock_classify_float_size.return_value = FloatClassification.LOW

    results = scan_stocks()

    assert len(results) == 1

    candidate = results[0]

    assert candidate.quote_data.symbol == "BIVI"
    assert candidate.quote_data.volume == 5_000
    assert candidate.quote_data.average_volume == 2_500.0
    assert candidate.quote_data.relative_volume == 2.0
    assert candidate.float_data == float_data
    assert candidate.float_turnover == 0.25
    assert candidate.float_classification == FloatClassification.LOW
    assert candidate.price_action is None

    mock_get_float_data.assert_called_once_with("BIVI")

    mock_calculate_float_turnover.assert_called_once_with(
        5_000,
        7_500_000,
    )

    mock_classify_float_size.assert_called_once_with(
        7_500_000,
    )


@patch("stonks.scanner.filters.WATCHLIST", ["BIVI"])
@patch("stonks.scanner.filters.MIN_VOLUME", 1_000)
@patch("stonks.scanner.filters.time.sleep")
@patch("stonks.scanner.filters.classify_float_size")
@patch("stonks.scanner.filters.calculate_float_turnover")
@patch("stonks.scanner.filters.calculate_relative_volume")
@patch("stonks.scanner.filters.calculate_average_volume")
@patch("stonks.scanner.filters.parse_historical_volumes")
@patch("stonks.scanner.filters.get_historical_data")
@patch("stonks.scanner.filters.get_intraday_data")
@patch("stonks.scanner.filters.get_float_data")
@patch("stonks.scanner.filters.get_quote")
def test_scan_stocks_keeps_candidate_when_float_data_unavailable(
    mock_get_quote,
    mock_get_float_data,
    mock_get_intraday_data,
    mock_get_historical_data,
    mock_parse_historical_volumes,
    mock_calculate_average_volume,
    mock_calculate_relative_volume,
    mock_calculate_float_turnover,
    mock_classify_float_size,
    mock_sleep,
):
    """Verify unavailable float data does not remove a qualifying stock."""

    mock_get_quote.return_value = build_quote_response(volume=5_000)
    mock_get_historical_data.return_value = {"historical": "data"}
    mock_parse_historical_volumes.return_value = []
    mock_calculate_average_volume.return_value = 2_500.0
    mock_calculate_relative_volume.return_value = 2.0
    mock_get_float_data.return_value = None
    mock_get_intraday_data.return_value = []

    results = scan_stocks()

    assert len(results) == 1

    candidate = results[0]

    assert candidate.quote_data.symbol == "BIVI"
    assert candidate.float_data is None
    assert candidate.float_turnover is None
    assert candidate.float_classification == FloatClassification.UNKNOWN
    assert candidate.price_action is None

    mock_get_float_data.assert_called_once_with("BIVI")
    mock_calculate_float_turnover.assert_not_called()
    mock_classify_float_size.assert_not_called()


@patch("stonks.scanner.filters.WATCHLIST", ["BIVI"])
@patch("stonks.scanner.filters.MIN_VOLUME", 1_000)
@patch("stonks.scanner.filters.time.sleep")
@patch("stonks.scanner.filters.calculate_relative_volume")
@patch("stonks.scanner.filters.calculate_average_volume")
@patch("stonks.scanner.filters.parse_historical_volumes")
@patch("stonks.scanner.filters.get_historical_data")
@patch("stonks.scanner.filters.get_intraday_data")
@patch("stonks.scanner.filters.get_float_data")
@patch("stonks.scanner.filters.get_quote")
def test_scan_stocks_does_not_request_enrichment_for_filtered_stock(
    mock_get_quote,
    mock_get_float_data,
    mock_get_intraday_data,
    mock_get_historical_data,
    mock_parse_historical_volumes,
    mock_calculate_average_volume,
    mock_calculate_relative_volume,
    mock_sleep,
):
    """Verify stocks failing the volume filter are not enriched."""

    mock_get_quote.return_value = build_quote_response(volume=500)
    mock_get_historical_data.return_value = {"historical": "data"}
    mock_parse_historical_volumes.return_value = []
    mock_calculate_average_volume.return_value = 2_500.0
    mock_calculate_relative_volume.return_value = 0.2

    results = scan_stocks()

    assert results == []

    mock_get_float_data.assert_not_called()
    mock_get_intraday_data.assert_not_called()


@patch("stonks.scanner.filters.WATCHLIST", ["BIVI"])
@patch("stonks.scanner.filters.MIN_VOLUME", 1_000)
@patch("stonks.scanner.filters.time.sleep")
@patch("stonks.scanner.filters.calculate_relative_volume")
@patch("stonks.scanner.filters.calculate_average_volume")
@patch("stonks.scanner.filters.parse_historical_volumes")
@patch("stonks.scanner.filters.get_historical_data")
@patch("stonks.scanner.filters.get_intraday_data")
@patch("stonks.scanner.filters.get_float_data")
@patch("stonks.scanner.filters.get_quote")
def test_scan_stocks_adds_price_action_to_candidate(
    mock_get_quote,
    mock_get_float_data,
    mock_get_intraday_data,
    mock_get_historical_data,
    mock_parse_historical_volumes,
    mock_calculate_average_volume,
    mock_calculate_relative_volume,
    mock_sleep,
):
    """Verify qualifying stocks receive regular-session price action."""

    mock_get_quote.return_value = build_quote_response(volume=5_000)
    mock_get_float_data.return_value = None
    mock_get_historical_data.return_value = {"historical": "data"}
    mock_parse_historical_volumes.return_value = []
    mock_calculate_average_volume.return_value = 2_500.0
    mock_calculate_relative_volume.return_value = 2.0

    candles = [
        build_candle(
            timestamp=datetime(
                2026,
                9,
                8,
                13,
                30,
                tzinfo=timezone.utc,
            ),
            open_price=10.00,
            high_price=10.50,
            low_price=9.75,
            close_price=10.25,
        ),
        build_candle(
            timestamp=datetime(
                2026,
                9,
                8,
                13,
                31,
                tzinfo=timezone.utc,
            ),
            open_price=10.25,
            high_price=11.00,
            low_price=10.20,
            close_price=10.75,
        ),
    ]

    mock_get_intraday_data.return_value = candles

    results = scan_stocks()

    assert len(results) == 1

    candidate = results[0]

    assert candidate.price_action is not None
    assert candidate.price_action.session == MarketSession.REGULAR

    assert candidate.price_action.session_data.change_percent == pytest.approx(7.5)
    assert candidate.price_action.session_data.high_price == pytest.approx(11.00)
    assert candidate.price_action.session_data.low_price == pytest.approx(9.75)

    assert set(candidate.price_action.lookbacks) == set(PRICE_ACTION_LOOKBACKS)

    mock_get_intraday_data.assert_called_once_with(
        symbol="BIVI",
        timeframe=Timeframe.ONE_MINUTE,
        start_date=date(2026, 9, 8),
        end_date=date(2026, 9, 8),
    )


@patch("stonks.scanner.filters.WATCHLIST", ["BIVI"])
@patch("stonks.scanner.filters.MIN_VOLUME", 1_000)
@patch("stonks.scanner.filters.time.sleep")
@patch("stonks.scanner.filters.calculate_relative_volume")
@patch("stonks.scanner.filters.calculate_average_volume")
@patch("stonks.scanner.filters.parse_historical_volumes")
@patch("stonks.scanner.filters.get_historical_data")
@patch("stonks.scanner.filters.get_intraday_data")
@patch("stonks.scanner.filters.get_float_data")
@patch("stonks.scanner.filters.get_quote")
def test_scan_stocks_keeps_candidate_when_intraday_data_unavailable(
    mock_get_quote,
    mock_get_float_data,
    mock_get_intraday_data,
    mock_get_historical_data,
    mock_parse_historical_volumes,
    mock_calculate_average_volume,
    mock_calculate_relative_volume,
    mock_sleep,
):
    """Verify unavailable intraday data does not remove a qualifying stock."""

    mock_get_quote.return_value = build_quote_response(volume=5_000)
    mock_get_float_data.return_value = None
    mock_get_historical_data.return_value = {"historical": "data"}
    mock_parse_historical_volumes.return_value = []
    mock_calculate_average_volume.return_value = 2_500.0
    mock_calculate_relative_volume.return_value = 2.0
    mock_get_intraday_data.return_value = []

    results = scan_stocks()

    assert len(results) == 1

    candidate = results[0]

    assert candidate.quote_data.symbol == "BIVI"
    assert candidate.price_action is None
