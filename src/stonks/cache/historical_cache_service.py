# =============================================================================
# File: historical_cache_service.py
# Purpose: Provides cache-aware access to historical market data.
#
# Notes:
# - Uses cached historical data when available.
# - Calls the external API only when cache is missing and API calls are allowed.
# - Designed to protect limited API request quotas.
# =============================================================================

from stonks.api.market_data import get_daily_time_series
from stonks.cache.cache_paths import HISTORICAL_CACHE_DIRECTORY
from stonks.cache.cache_paths import ensure_cache_directories_exist
from stonks.cache.json_cache import read_json
from stonks.cache.json_cache import write_json
from stonks.config.settings import ALLOW_API_CALLS
from stonks.config.settings import USE_CACHE

def get_historical_data(symbol: str):
    """Get historical data for a symbol using cache-first logic."""

    ensure_cache_directories_exist()

    cache_file = HISTORICAL_CACHE_DIRECTORY / f"{symbol.upper()}_daily.json"

    if USE_CACHE:
        cached_data = read_json(cache_file)

        if cached_data:
            print(f"Using cached historical data for {symbol.upper()}")
            return cached_data

    if not ALLOW_API_CALLS:
        print(
            f"API calls disabled and no cache found for {symbol.upper()}."
        )
        return None

    print(f"Fetching historical data for {symbol.upper()} from API...")

    data = get_daily_time_series(symbol.upper())

    if data and USE_CACHE:
        write_json(cache_file, data)

    return data