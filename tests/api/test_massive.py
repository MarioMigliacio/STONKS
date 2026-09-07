# =============================================================================
# File: test_massive.py
# Purpose: Tests Massive public-float API integration.
# =============================================================================

from datetime import date
from unittest.mock import Mock, patch

import pytest

from stonks.api.massive import get_float, require_api_key


@patch("stonks.api.massive.settings.MASSIVE_API_KEY", "test-api-key")
@patch("stonks.api.massive.requests.get")
def test_get_float_returns_float_data(mock_get):
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
    response = Mock()
    response.status_code = 500

    mock_get.return_value = response

    assert get_float("BIVI") is None


@patch("stonks.api.massive.settings.MASSIVE_API_KEY", None)
def test_require_api_key_raises_when_key_is_missing():
    with pytest.raises(RuntimeError):
        require_api_key()
