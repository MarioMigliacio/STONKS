# =============================================================================
# File: test_massive.py
# Purpose: Tests Massive market-data API integration.
# =============================================================================

from datetime import date, datetime, timezone
from unittest.mock import Mock, patch

import pytest

from stonks.api.massive import get_aggregate_bars, get_float, require_api_key
from stonks.models.timeframe import Timeframe


@patch("stonks.api.massive.settings.MASSIVE_API_KEY", "test-api-key")
@patch("stonks.api.massive.requests.get")
def test_get_float_returns_float_data(mock_get):
    """Verify a valid Massive response is converted into FloatData."""

    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "status": "OK",
        "results": [
            {
                "ticker": "BIVI",
                "effective_date": "2026-08-20",
                "free_float": 7_500_000,
                "free_float_percent": 62.5,
            }
        ],
    }

    mock_get.return_value = response

    float_data = get_float("bivi")

    assert float_data is not None
    assert float_data.symbol == "BIVI"
    assert float_data.float_shares == 7_500_000
    assert float_data.float_percent == 62.5
    assert float_data.effective_date == date(2026, 8, 20)
    assert float_data.source == "Massive"

    mock_get.assert_called_once()

    _, kwargs = mock_get.call_args

    assert kwargs["params"]["ticker"] == "BIVI"
    assert "apiKey" not in kwargs["params"]
    assert kwargs["headers"]["Authorization"] == "Bearer test-api-key"
    assert kwargs["timeout"] == 15


@patch("stonks.api.massive.settings.MASSIVE_API_KEY", "test-api-key")
@patch("stonks.api.massive.requests.get")
def test_get_float_returns_none_when_results_are_empty(mock_get):
    """Verify missing Massive float results return None."""

    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "status": "OK",
        "results": [],
    }

    mock_get.return_value = response

    assert get_float("BIVI") is None


@patch("stonks.api.massive.settings.MASSIVE_API_KEY", "test-api-key")
@patch("stonks.api.massive.requests.get")
def test_get_float_returns_none_when_request_fails(mock_get):
    """Verify a failed Massive request returns None."""

    response = Mock()
    response.status_code = 500

    mock_get.return_value = response

    assert get_float("BIVI") is None


@patch("stonks.api.massive.settings.MASSIVE_API_KEY", None)
def test_require_api_key_raises_when_key_is_missing():
    """Verify Massive requests require a configured API key."""

    with pytest.raises(RuntimeError):
        require_api_key()


@patch("stonks.api.massive.settings.MASSIVE_API_KEY", "test-api-key")
@patch("stonks.api.massive.requests.get")
def test_get_aggregate_bars_returns_candle_data(mock_get):
    """Verify valid Massive aggregate bars are converted into CandleData."""

    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "status": "OK",
        "results": [
            {
                "t": 1789061400000,
                "o": 10.25,
                "h": 10.75,
                "l": 10.10,
                "c": 10.60,
                "v": 125_000,
            }
        ],
    }

    mock_get.return_value = response

    candles = get_aggregate_bars(
        "bivi",
        Timeframe.FIVE_MINUTES,
        date(2026, 9, 10),
        date(2026, 9, 10),
    )

    assert len(candles) == 1

    candle = candles[0]

    assert candle.timestamp == datetime.fromtimestamp(
        1789061400000 / 1000,
        tz=timezone.utc,
    )
    assert candle.open_price == 10.25
    assert candle.high_price == 10.75
    assert candle.low_price == 10.10
    assert candle.close_price == 10.60
    assert candle.volume == 125_000

    mock_get.assert_called_once()

    args, kwargs = mock_get.call_args

    assert "/BIVI/range/5/minute/2026-09-10/2026-09-10" in args[0]
    assert kwargs["params"]["adjusted"] == "true"
    assert kwargs["params"]["sort"] == "asc"
    assert kwargs["params"]["limit"] == 50000
    assert kwargs["headers"]["Authorization"] == "Bearer test-api-key"
    assert kwargs["timeout"] == 15


@patch("stonks.api.massive.settings.MASSIVE_API_KEY", "test-api-key")
@patch("stonks.api.massive.requests.get")
def test_get_aggregate_bars_returns_empty_list_when_results_are_empty(mock_get):
    """Verify missing Massive aggregate results return an empty list."""

    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "status": "OK",
        "results": [],
    }

    mock_get.return_value = response

    candles = get_aggregate_bars(
        "BIVI",
        Timeframe.ONE_MINUTE,
        date(2026, 9, 10),
        date(2026, 9, 10),
    )

    assert candles == []


@patch("stonks.api.massive.settings.MASSIVE_API_KEY", "test-api-key")
@patch("stonks.api.massive.requests.get")
def test_get_aggregate_bars_returns_empty_list_when_request_fails(mock_get):
    """Verify a failed Massive aggregate request returns an empty list."""

    response = Mock()
    response.status_code = 500

    mock_get.return_value = response

    candles = get_aggregate_bars(
        "BIVI",
        Timeframe.ONE_MINUTE,
        date(2026, 9, 10),
        date(2026, 9, 10),
    )

    assert candles == []
