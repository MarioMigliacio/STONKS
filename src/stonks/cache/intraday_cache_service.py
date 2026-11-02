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
from stonks.models.historical_research_result import ResearchDataSource
from stonks.models.research_data_retrieval import (
    ResearchDataRetrieval,
    ResearchRetrievalStatus,
)
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


def _validate_research_cache(
    data: dict,
    symbol: str,
    timeframe: Timeframe,
    start_date: date,
    end_date: date,
) -> list[CandleData]:
    """Validate cache identity and normalize its stored candles."""
    if not isinstance(data, dict):
        raise ValueError("Invalid intraday cache structure.")

    if (
        data.get("symbol") != symbol
        or data.get("timeframe") != timeframe.value
        or data.get("start_date") != start_date.isoformat()
        or data.get("end_date") != end_date.isoformat()
    ):
        raise ValueError("Intraday cache metadata does not match the request.")

    if not isinstance(data.get("candles"), list):
        raise ValueError("Invalid intraday cache candle collection.")

    candles = _parse_cached_data(data)

    for candle in candles:
        timestamp = candle.timestamp

        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("Cached candle timestamp must be timezone-aware.")

        if (
            candle.low_price <= 0
            or candle.high_price < candle.low_price
            or candle.high_price < max(candle.open_price, candle.close_price)
            or candle.low_price > min(candle.open_price, candle.close_price)
            or candle.volume < 0
        ):
            raise ValueError("Invalid cached candle OHLCV values.")

    return candles


def retrieve_intraday_data(
    symbol: str,
    timeframe: Timeframe,
    start_date: date,
    end_date: date,
    force_refresh: bool = False,
) -> ResearchDataRetrieval:
    """
    Retrieve intraday candles with explicit provenance and failure status.

    Existing cache serialization and paths are reused. Provider failures
    never silently fall back to stale cached data.
    """
    ensure_cache_directories_exist()

    symbol = symbol.strip().upper()

    if not symbol:
        raise ValueError("Intraday research symbol cannot be empty.")

    if start_date > end_date:
        raise ValueError("Start date must not exceed end date.")

    cache_file = _build_cache_file(
        symbol,
        timeframe,
        start_date,
        end_date,
    )

    if USE_CACHE and not force_refresh:
        try:
            cached_data = read_json(cache_file)

            if cached_data is not None:
                candles = _validate_research_cache(
                    cached_data,
                    symbol,
                    timeframe,
                    start_date,
                    end_date,
                )

                if candles:
                    return ResearchDataRetrieval(
                        candles=candles,
                        status=ResearchRetrievalStatus.SUCCESS,
                        source=ResearchDataSource.CACHE,
                    )

                # A cached empty collection is not treated as an
                # authoritative no-data response.
                logger.warning(
                    "Empty intraday cache for %s; checking provider.",
                    symbol,
                )

        except (OSError, ValueError, KeyError, TypeError) as exc:
            logger.warning(
                "Invalid intraday research cache for %s: %s",
                symbol,
                exc,
            )

            # Do not hide cache corruption when API calls are disabled.
            if not ALLOW_API_CALLS:
                return ResearchDataRetrieval(
                    candles=[],
                    status=ResearchRetrievalStatus.PROVIDER_ERROR,
                    message="Local intraday cache is invalid or unreadable.",
                )

    if not ALLOW_API_CALLS:
        return ResearchDataRetrieval(
            candles=[],
            status=ResearchRetrievalStatus.API_DISABLED,
            message="API calls are disabled and no usable cache is available.",
        )

    try:
        candles = get_aggregate_bars(
            symbol,
            timeframe,
            start_date,
            end_date,
            raise_on_error=True,
        )

    except (RuntimeError, ValueError, OSError) as exc:
        logger.warning(
            "Intraday research provider failure for %s: %s",
            symbol,
            exc,
        )

        return ResearchDataRetrieval(
            candles=[],
            status=ResearchRetrievalStatus.PROVIDER_ERROR,
            source=ResearchDataSource.PROVIDER,
            message=str(exc),
        )

    if not candles:
        return ResearchDataRetrieval(
            candles=[],
            status=ResearchRetrievalStatus.NO_DATA,
            source=ResearchDataSource.PROVIDER,
            message="No intraday candles were returned for this period.",
        )

    if USE_CACHE:
        try:
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
        except (OSError, TypeError, ValueError) as exc:
            logger.warning(
                "Could not cache intraday research data for %s: %s",
                symbol,
                exc,
            )

    return ResearchDataRetrieval(
        candles=candles,
        status=ResearchRetrievalStatus.SUCCESS,
        source=ResearchDataSource.PROVIDER,
    )
