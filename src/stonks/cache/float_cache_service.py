# =============================================================================
# File: float_cache_service.py
# Purpose: Provides cache-aware access to public-float data.
#
# Notes:
# - Uses cached float data when available and fresh.
# - Refreshes stale or missing data when API calls are allowed.
# - Preserves provider effective date separately from cache timestamp.
# =============================================================================

import logging
from datetime import date, datetime, timezone
from typing import Optional

from stonks.api.massive import get_float
from stonks.cache.cache_paths import (
    FLOAT_CACHE_DIRECTORY,
    ensure_cache_directories_exist,
)
from stonks.cache.json_cache import read_json, write_json
from stonks.config.settings import (
    ALLOW_API_CALLS,
    ENABLE_FLOAT_DATA,
    FLOAT_CACHE_MAX_AGE_DAYS,
    USE_CACHE,
)
from stonks.models.float_data import FloatData

logger = logging.getLogger(__name__)


def get_float_data(symbol: str, force_refresh: bool = False) -> Optional[FloatData]:
    """Get float data for a symbol using cache-first logic."""

    symbol = symbol.upper()

    if not ENABLE_FLOAT_DATA:
        logger.debug(
            "Float data disabled for %s",
            symbol,
        )
        return None

    ensure_cache_directories_exist()

    cache_file = FLOAT_CACHE_DIRECTORY / f"{symbol}_float.json"

    if force_refresh:
        logger.debug(
            "Force refresh requested for float data: %s",
            symbol,
        )

    if USE_CACHE and not force_refresh:
        cached_data = read_json(cache_file)

        if cached_data and _is_cache_fresh(cached_data):
            logger.debug(
                "Using cached float data for %s",
                symbol,
            )
            return _parse_cached_float_data(cached_data)

    if not ALLOW_API_CALLS:
        logger.warning(
            "API calls disabled and no fresh cached float data found for %s",
            symbol,
        )
        return None

    logger.debug(
        "Fetching float data from Massive for %s",
        symbol,
    )

    float_data = get_float(symbol)

    if float_data is None:
        return None

    if USE_CACHE:
        logger.debug(
            "Caching float data for %s",
            symbol,
        )
        write_json(
            cache_file,
            _build_cache_data(float_data),
        )

    return float_data


def _build_cache_data(float_data: FloatData) -> dict:
    """Convert FloatData into JSON-compatible cache data."""

    return {
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "symbol": float_data.symbol,
        "float_shares": float_data.float_shares,
        "float_percent": float_data.float_percent,
        "effective_date": float_data.effective_date.isoformat(),
        "source": float_data.source,
    }


def _parse_cached_float_data(data: dict) -> FloatData:
    """Convert cached JSON data into FloatData."""

    return FloatData(
        symbol=data["symbol"],
        float_shares=data["float_shares"],
        float_percent=data["float_percent"],
        effective_date=date.fromisoformat(data["effective_date"]),
        source=data["source"],
    )


def _is_cache_fresh(data: dict) -> bool:
    """Return whether cached float data is still within its allowed age."""

    cached_at_text = data.get("cached_at")

    if not cached_at_text:
        return False

    cached_at = datetime.fromisoformat(cached_at_text)
    cache_age = datetime.now(timezone.utc) - cached_at

    return cache_age.days < FLOAT_CACHE_MAX_AGE_DAYS
