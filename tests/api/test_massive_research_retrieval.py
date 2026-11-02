# =============================================================================
# File: test_massive_research_retrieval.py
# Purpose: Tests strict Massive aggregate retrieval and error handling.
# =============================================================================

from datetime import date
from unittest.mock import Mock, patch

import pytest
import requests

from stonks.api.massive import get_aggregate_bars
from stonks.models.timeframe import Timeframe

START_DATE = date(2026, 9, 28)
END_DATE = date(2026, 9, 28)


def fetch_bars(raise_on_error: bool = False):
    """Request test aggregates using the configured strictness."""
    return get_aggregate_bars(
        "AAPL",
        Timeframe.ONE_MINUTE,
        START_DATE,
        END_DATE,
        raise_on_error=raise_on_error,
    )


@patch("stonks.api.massive.require_api_key", return_value="test-key")
@patch("stonks.api.massive.requests.get")
def test_valid_empty_response(mock_get: Mock, mock_key: Mock) -> None:
    """A valid empty provider response is not an error."""
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "status": "OK",
        "results": [],
    }

    assert fetch_bars(raise_on_error=True) == []


@patch("stonks.api.massive.require_api_key", return_value="test-key")
@patch("stonks.api.massive.requests.get")
def test_successful_candles(mock_get: Mock, mock_key: Mock) -> None:
    """Valid provider candles should be normalized."""
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "status": "OK",
        "results": [
            {
                "t": 1790602200000,
                "o": 100.0,
                "h": 105.0,
                "l": 99.0,
                "c": 103.0,
                "v": 1000,
            }
        ],
    }

    candles = fetch_bars(raise_on_error=True)

    assert len(candles) == 1
    assert candles[0].open_price == 100.0
    assert candles[0].close_price == 103.0
    assert candles[0].volume == 1000


@patch("stonks.api.massive.require_api_key", return_value="test-key")
@patch("stonks.api.massive.requests.get")
def test_http_failure_raises_in_strict_mode(
    mock_get: Mock,
    mock_key: Mock,
) -> None:
    """Strict retrieval must expose HTTP failures."""
    mock_get.return_value.status_code = 429

    with pytest.raises(RuntimeError, match="retrieval failed"):
        fetch_bars(raise_on_error=True)


@patch("stonks.api.massive.require_api_key", return_value="test-key")
@patch("stonks.api.massive.requests.get")
def test_http_failure_preserves_legacy_behavior(
    mock_get: Mock,
    mock_key: Mock,
) -> None:
    """Existing callers should still receive an empty list."""
    mock_get.return_value.status_code = 500

    assert fetch_bars() == []


@patch("stonks.api.massive.require_api_key", return_value="test-key")
@patch("stonks.api.massive.requests.get")
def test_network_failure_raises_in_strict_mode(
    mock_get: Mock,
    mock_key: Mock,
) -> None:
    """Network failures must be distinguishable from empty data."""
    mock_get.side_effect = requests.Timeout("Request timed out")

    with pytest.raises(RuntimeError, match="retrieval failed"):
        fetch_bars(raise_on_error=True)


@patch("stonks.api.massive.require_api_key", return_value="test-key")
@patch("stonks.api.massive.requests.get")
def test_provider_error_payload_raises(
    mock_get: Mock,
    mock_key: Mock,
) -> None:
    """Provider-reported errors must not appear as no-data results."""
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "status": "ERROR",
        "error": "Request rejected",
    }

    with pytest.raises(RuntimeError, match="retrieval failed"):
        fetch_bars(raise_on_error=True)
