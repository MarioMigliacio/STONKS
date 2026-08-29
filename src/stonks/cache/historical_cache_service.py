# =============================================================================
# File: historical_cache_service.py
# Purpose: Provides cache-aware access to historical market data.
#
# Notes:
# - Uses cached historical data when available.
# - Calls the external API only when cache is missing and API calls are allowed.
# - Designed to protect limited API request quotas.
# =============================================================================

import logging

from stonks.api.market_data import get_daily_time_series
from stonks.cache.cache_paths import (
    HISTORICAL_CACHE_DIRECTORY,
    ensure_cache_directories_exist,
)
from stonks.cache.json_cache import read_json, write_json
from stonks.config.settings import ALLOW_API_CALLS, USE_CACHE

logger = logging.getLogger(__name__)


def get_historical_data(symbol: str, force_refresh: bool = False):
    """Get historical data for a symbol using cache-first logic."""

    ensure_cache_directories_exist()

    symbol = symbol.upper()

    cache_file = HISTORICAL_CACHE_DIRECTORY / f"{symbol}_daily.json"

    if force_refresh:
        logger.debug(
            "Force refresh requested for %s",
            symbol,
        )

    if USE_CACHE and not force_refresh:
        cached_data = read_json(cache_file)

        if cached_data:
            logger.debug(
                "Using cached historical data for %s",
                symbol,
            )
            return cached_data

    if not ALLOW_API_CALLS:
        logger.warning(
            "API calls disabled and no cached historical data found for %s",
            symbol,
        )
        return None

    logger.debug(
        "Fetching historical data from API for %s",
        symbol,
    )

    data = get_daily_time_series(symbol)

    if data and USE_CACHE:
        logger.debug(
            "Caching historical data for %s",
            symbol,
        )
        write_json(cache_file, data)

    return data
