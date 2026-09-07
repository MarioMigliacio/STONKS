# =============================================================================
# File: test_float_cache_service.py
# Purpose: Tests cache-aware public-float data retrieval.
# =============================================================================

from datetime import date, datetime, timezone
from unittest.mock import patch

from stonks.cache.float_cache_service import (
    _build_cache_data,
    _is_cache_fresh,
    _parse_cached_float_data,
    get_float_data,
)
from stonks.models.float_data import FloatData


def build_float_data() -> FloatData:
    """Build reusable FloatData for cache service tests."""

    return FloatData(
        symbol="BIVI",
        float_shares=7_500_000,
        float_percent=62.5,
        effective_date=date(2026, 8, 20),
        source="Massive",
    )


@patch("stonks.cache.float_cache_service.ENABLE_FLOAT_DATA", False)
@patch("stonks.cache.float_cache_service.get_float")
def test_get_float_data_returns_none_when_feature_disabled(mock_get_float):
    """Verify disabled float support returns None without calling Massive."""

    result = get_float_data("bivi")

    assert result is None
    mock_get_float.assert_not_called()


@patch("stonks.cache.float_cache_service.ENABLE_FLOAT_DATA", True)
@patch("stonks.cache.float_cache_service.USE_CACHE", True)
@patch("stonks.cache.float_cache_service.read_json")
@patch("stonks.cache.float_cache_service.get_float")
def test_get_float_data_returns_fresh_cached_data(
    mock_get_float,
    mock_read_json,
):
    """Verify fresh cached float data is used without calling Massive."""

    mock_read_json.return_value = {
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "symbol": "BIVI",
        "float_shares": 7_500_000,
        "float_percent": 62.5,
        "effective_date": "2026-08-20",
        "source": "Massive",
    }

    result = get_float_data("bivi")

    assert result is not None
    assert result.symbol == "BIVI"
    assert result.float_shares == 7_500_000
    assert result.float_percent == 62.5
    assert result.effective_date == date(2026, 8, 20)
    assert result.source == "Massive"

    mock_get_float.assert_not_called()


@patch("stonks.cache.float_cache_service.ENABLE_FLOAT_DATA", True)
@patch("stonks.cache.float_cache_service.USE_CACHE", True)
@patch("stonks.cache.float_cache_service.ALLOW_API_CALLS", True)
@patch("stonks.cache.float_cache_service.write_json")
@patch("stonks.cache.float_cache_service.read_json")
@patch("stonks.cache.float_cache_service.get_float")
def test_get_float_data_fetches_when_cache_missing(
    mock_get_float,
    mock_read_json,
    mock_write_json,
):
    """Verify missing cache data is fetched from Massive and cached."""

    float_data = build_float_data()

    mock_read_json.return_value = None
    mock_get_float.return_value = float_data

    result = get_float_data("bivi")

    assert result == float_data

    mock_get_float.assert_called_once_with("BIVI")
    mock_write_json.assert_called_once()


@patch("stonks.cache.float_cache_service.ENABLE_FLOAT_DATA", True)
@patch("stonks.cache.float_cache_service.USE_CACHE", True)
@patch("stonks.cache.float_cache_service.ALLOW_API_CALLS", True)
@patch("stonks.cache.float_cache_service.write_json")
@patch("stonks.cache.float_cache_service.read_json")
@patch("stonks.cache.float_cache_service.get_float")
def test_get_float_data_refreshes_stale_cache(
    mock_get_float,
    mock_read_json,
    mock_write_json,
):
    """Verify stale cached float data is refreshed through Massive."""

    float_data = build_float_data()

    mock_read_json.return_value = {
        "cached_at": "2026-01-01T00:00:00+00:00",
        "symbol": "BIVI",
        "float_shares": 6_000_000,
        "float_percent": 50.0,
        "effective_date": "2026-01-01",
        "source": "Massive",
    }

    mock_get_float.return_value = float_data

    result = get_float_data("BIVI")

    assert result == float_data

    mock_get_float.assert_called_once_with("BIVI")
    mock_write_json.assert_called_once()


@patch("stonks.cache.float_cache_service.ENABLE_FLOAT_DATA", True)
@patch("stonks.cache.float_cache_service.USE_CACHE", True)
@patch("stonks.cache.float_cache_service.ALLOW_API_CALLS", False)
@patch("stonks.cache.float_cache_service.read_json")
@patch("stonks.cache.float_cache_service.get_float")
def test_get_float_data_returns_none_when_api_calls_disabled(
    mock_get_float,
    mock_read_json,
):
    """Verify missing cache data returns None when API calls are disabled."""

    mock_read_json.return_value = None

    result = get_float_data("BIVI")

    assert result is None
    mock_get_float.assert_not_called()


@patch("stonks.cache.float_cache_service.ENABLE_FLOAT_DATA", True)
@patch("stonks.cache.float_cache_service.USE_CACHE", True)
@patch("stonks.cache.float_cache_service.ALLOW_API_CALLS", True)
@patch("stonks.cache.float_cache_service.write_json")
@patch("stonks.cache.float_cache_service.read_json")
@patch("stonks.cache.float_cache_service.get_float")
def test_get_float_data_does_not_cache_failed_request(
    mock_get_float,
    mock_read_json,
    mock_write_json,
):
    """Verify unsuccessful Massive retrievals are not written to cache."""

    mock_read_json.return_value = None
    mock_get_float.return_value = None

    result = get_float_data("BIVI")

    assert result is None
    mock_write_json.assert_not_called()


@patch("stonks.cache.float_cache_service.ENABLE_FLOAT_DATA", True)
@patch("stonks.cache.float_cache_service.USE_CACHE", True)
@patch("stonks.cache.float_cache_service.ALLOW_API_CALLS", True)
@patch("stonks.cache.float_cache_service.write_json")
@patch("stonks.cache.float_cache_service.read_json")
@patch("stonks.cache.float_cache_service.get_float")
def test_get_float_data_force_refresh_bypasses_cache(
    mock_get_float,
    mock_read_json,
    mock_write_json,
):
    """Verify force refresh bypasses the cache and retrieves fresh float data."""

    float_data = build_float_data()
    mock_get_float.return_value = float_data

    result = get_float_data(
        "bivi",
        force_refresh=True,
    )

    assert result == float_data

    mock_read_json.assert_not_called()
    mock_get_float.assert_called_once_with("BIVI")
    mock_write_json.assert_called_once()


def test_build_and_parse_cache_data_round_trip():
    """Verify FloatData survives cache serialization and deserialization."""

    float_data = build_float_data()

    cached_data = _build_cache_data(float_data)
    parsed_data = _parse_cached_float_data(cached_data)

    assert parsed_data == float_data
    assert "cached_at" in cached_data


def test_is_cache_fresh_returns_false_without_cached_at():
    """Verify cache data without a cache timestamp is considered stale."""

    cached_data = {
        "symbol": "BIVI",
    }

    assert _is_cache_fresh(cached_data) is False
