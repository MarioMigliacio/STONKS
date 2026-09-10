# =============================================================================
# File: test_filters.py
# Purpose: Pytest file for test_filters.py.
# =============================================================================

from datetime import date
from unittest.mock import patch

from stonks.models.float_data import FloatData
from stonks.scanner.filters import scan_stocks


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


@patch("stonks.scanner.filters.WATCHLIST", ["BIVI"])
@patch("stonks.scanner.filters.MIN_VOLUME", 1_000)
@patch("stonks.scanner.filters.time.sleep")
@patch("stonks.scanner.filters.calculate_relative_volume")
@patch("stonks.scanner.filters.calculate_average_volume")
@patch("stonks.scanner.filters.parse_historical_volumes")
@patch("stonks.scanner.filters.get_historical_data")
@patch("stonks.scanner.filters.get_float_data")
@patch("stonks.scanner.filters.get_quote")
def test_scan_stocks_adds_float_data_to_candidate(
    mock_get_quote,
    mock_get_float_data,
    mock_get_historical_data,
    mock_parse_historical_volumes,
    mock_calculate_average_volume,
    mock_calculate_relative_volume,
    mock_sleep,
):
    """Verify a qualifying stock is returned with available float data."""

    float_data = build_float_data()

    mock_get_quote.return_value = build_quote_response(volume=5_000)
    mock_get_historical_data.return_value = {"historical": "data"}
    mock_parse_historical_volumes.return_value = []
    mock_calculate_average_volume.return_value = 2_500.0
    mock_calculate_relative_volume.return_value = 2.0
    mock_get_float_data.return_value = float_data

    results = scan_stocks()

    assert len(results) == 1

    candidate = results[0]

    assert candidate.quote_data.symbol == "BIVI"
    assert candidate.quote_data.volume == 5_000
    assert candidate.quote_data.average_volume == 2_500.0
    assert candidate.quote_data.relative_volume == 2.0
    assert candidate.float_data == float_data

    mock_get_float_data.assert_called_once_with("BIVI")


@patch("stonks.scanner.filters.WATCHLIST", ["BIVI"])
@patch("stonks.scanner.filters.MIN_VOLUME", 1_000)
@patch("stonks.scanner.filters.time.sleep")
@patch("stonks.scanner.filters.calculate_relative_volume")
@patch("stonks.scanner.filters.calculate_average_volume")
@patch("stonks.scanner.filters.parse_historical_volumes")
@patch("stonks.scanner.filters.get_historical_data")
@patch("stonks.scanner.filters.get_float_data")
@patch("stonks.scanner.filters.get_quote")
def test_scan_stocks_keeps_candidate_when_float_data_unavailable(
    mock_get_quote,
    mock_get_float_data,
    mock_get_historical_data,
    mock_parse_historical_volumes,
    mock_calculate_average_volume,
    mock_calculate_relative_volume,
    mock_sleep,
):
    """Verify unavailable float data does not remove a qualifying stock."""

    mock_get_quote.return_value = build_quote_response(volume=5_000)
    mock_get_historical_data.return_value = {"historical": "data"}
    mock_parse_historical_volumes.return_value = []
    mock_calculate_average_volume.return_value = 2_500.0
    mock_calculate_relative_volume.return_value = 2.0
    mock_get_float_data.return_value = None

    results = scan_stocks()

    assert len(results) == 1

    candidate = results[0]

    assert candidate.quote_data.symbol == "BIVI"
    assert candidate.float_data is None

    mock_get_float_data.assert_called_once_with("BIVI")


@patch("stonks.scanner.filters.WATCHLIST", ["BIVI"])
@patch("stonks.scanner.filters.MIN_VOLUME", 1_000)
@patch("stonks.scanner.filters.time.sleep")
@patch("stonks.scanner.filters.calculate_relative_volume")
@patch("stonks.scanner.filters.calculate_average_volume")
@patch("stonks.scanner.filters.parse_historical_volumes")
@patch("stonks.scanner.filters.get_historical_data")
@patch("stonks.scanner.filters.get_float_data")
@patch("stonks.scanner.filters.get_quote")
def test_scan_stocks_does_not_request_float_for_filtered_stock(
    mock_get_quote,
    mock_get_float_data,
    mock_get_historical_data,
    mock_parse_historical_volumes,
    mock_calculate_average_volume,
    mock_calculate_relative_volume,
    mock_sleep,
):
    """Verify stocks failing the volume filter are not enriched with float data."""

    mock_get_quote.return_value = build_quote_response(volume=500)
    mock_get_historical_data.return_value = {"historical": "data"}
    mock_parse_historical_volumes.return_value = []
    mock_calculate_average_volume.return_value = 2_500.0
    mock_calculate_relative_volume.return_value = 0.2

    results = scan_stocks()

    assert results == []

    mock_get_float_data.assert_not_called()
