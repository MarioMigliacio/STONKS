# =============================================================================
# File: intraday_cache_service.py
# Purpose: Provides cache-aware access to intraday market data.
#
# Notes:
# - Uses cached intraday data when available.
# - Calls the external API only when cache is missing and API calls are allowed.
# - Designed to protect limited API request quotas.
# =============================================================================

import logging
from datetime import date, datetime
from pathlib import Path

from stonks.api.massive import get_aggregate_bars
from stonks.cache.cache_paths import (
    INTRADAY_CACHE_DIRECTORY,
    ensure_cache_directories_exist,
)
from stonks.cache.json_cache import read_json, write_json
from stonks.config.settings import ALLOW_API_CALLS, USE_CACHE
from stonks.models.candle_data import CandleData
from stonks.models.timeframe import Timeframe

logger = logging.getLogger(__name__)


def get_intraday_data(
    symbol: str,
    timeframe: Timeframe,
    start_date: date,
    end_date: date,
    force_refresh: bool = False,
) -> list[CandleData]:
    """Get intraday data for a symbol using cache-first logic."""

    ensure_cache_directories_exist()

    symbol = symbol.upper()

    cache_file = _build_cache_file(
        symbol,
        timeframe,
        start_date,
        end_date,
    )

    if force_refresh:
        logger.debug(
            "Force refresh requested for intraday data: %s",
            symbol,
        )

    if USE_CACHE and not force_refresh:
        cached_data = read_json(cache_file)

        if cached_data:
            logger.debug(
                "Using cached intraday data for %s",
                symbol,
            )
            return _parse_cached_data(cached_data)

    if not ALLOW_API_CALLS:
        logger.warning(
            "API calls disabled and no cached intraday data found for %s",
            symbol,
        )
        return []

    logger.debug(
        "Fetching %s intraday data from Massive for %s",
        timeframe.value,
        symbol,
    )

    candles = get_aggregate_bars(
        symbol,
        timeframe,
        start_date,
        end_date,
    )

    if candles and USE_CACHE:
        logger.debug(
            "Caching %s intraday data for %s",
            timeframe.value,
            symbol,
        )

        write_json(
            cache_file,
            _build_cache_data(
                symbol,
                timeframe,
                start_date,
                end_date,
                candles,
            ),
        )

    return candles


def _build_cache_data(
    symbol: str,
    timeframe: Timeframe,
    start_date: date,
    end_date: date,
    candles: list[CandleData],
) -> dict:
    """Convert intraday candle data into JSON-compatible cache data."""

    return {
        "symbol": symbol,
        "timeframe": timeframe.value,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "candles": [
            {
                "timestamp": candle.timestamp.isoformat(),
                "open_price": candle.open_price,
                "high_price": candle.high_price,
                "low_price": candle.low_price,
                "close_price": candle.close_price,
                "volume": candle.volume,
            }
            for candle in candles
        ],
    }


def _parse_cached_data(data: dict) -> list[CandleData]:
    """Convert cached intraday data into CandleData objects."""

    return [
        CandleData(
            timestamp=datetime.fromisoformat(candle["timestamp"]),
            open_price=candle["open_price"],
            high_price=candle["high_price"],
            low_price=candle["low_price"],
            close_price=candle["close_price"],
            volume=candle["volume"],
        )
        for candle in data["candles"]
    ]


def _build_cache_file(
    symbol: str,
    timeframe: Timeframe,
    start_date: date,
    end_date: date,
) -> Path:
    """Build the cache file path for an intraday data request."""

    return INTRADAY_CACHE_DIRECTORY / (
        f"{symbol}_{timeframe.value}_{start_date.isoformat()}_{end_date.isoformat()}.json"
    )
