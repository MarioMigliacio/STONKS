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
from datetime import date

from stonks.api.market_data import get_daily_time_series
from stonks.cache.cache_paths import (
    HISTORICAL_CACHE_DIRECTORY,
    ensure_cache_directories_exist,
)
from stonks.cache.json_cache import read_json, write_json
from stonks.config.settings import ALLOW_API_CALLS, USE_CACHE
from stonks.models.historical_research_result import ResearchDataSource
from stonks.models.research_data_retrieval import (
    ResearchDataRetrieval,
    ResearchRetrievalStatus,
)
from stonks.price_action.daily_candle_normalizer import normalize_daily_candles

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


def retrieve_daily_research_data(
    symbol: str,
    start_date: date,
    end_date: date,
    force_refresh: bool = False,
) -> ResearchDataRetrieval:
    """Retrieve normalized daily candles using the existing cache."""
    if start_date > end_date:
        raise ValueError("Start date must not exceed end date.")

    symbol = symbol.strip().upper()

    if not symbol:
        raise ValueError("Research symbol cannot be empty.")

    ensure_cache_directories_exist()
    cache_file = HISTORICAL_CACHE_DIRECTORY / f"{symbol}_daily.json"

    if USE_CACHE and not force_refresh:
        try:
            cached_data = read_json(cache_file)

            if cached_data is not None:
                # Validate the complete cached series before filtering
                # to the requested dates.
                series = cached_data.get("Time Series (Daily)")

                if not isinstance(series, dict):
                    raise ValueError("Invalid daily cache payload.")

                all_dates = [date.fromisoformat(key) for key in series]

                if all_dates:
                    normalize_daily_candles(
                        cached_data,
                        min(all_dates),
                        max(all_dates),
                    )

                candles = normalize_daily_candles(
                    cached_data,
                    start_date,
                    end_date,
                )

                if candles:
                    return ResearchDataRetrieval(
                        candles=candles,
                        status=ResearchRetrievalStatus.SUCCESS,
                        source=ResearchDataSource.CACHE,
                    )

                # A valid cache may simply lack the requested period.
                # Try the provider if API access is permitted.
                logger.debug(
                    "Daily cache has no requested candles for %s.",
                    symbol,
                )

        except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
            logger.warning(
                "Invalid daily research cache for %s: %s",
                symbol,
                exc,
            )

            if not ALLOW_API_CALLS:
                return ResearchDataRetrieval(
                    candles=[],
                    status=ResearchRetrievalStatus.CACHE_ERROR,
                    message="Local daily cache is invalid or unreadable.",
                )

    if not ALLOW_API_CALLS:
        return ResearchDataRetrieval(
            candles=[],
            status=ResearchRetrievalStatus.API_DISABLED,
            message="API calls are disabled and no usable daily cache exists.",
        )

    try:
        data = get_daily_time_series(
            symbol,
            raise_on_error=True,
        )

        # The normalizer validates OHLCV values and date formats.
        # Validate the full returned series before caching it.
        series = data.get("Time Series (Daily)")

        if not isinstance(series, dict):
            raise ValueError("Invalid daily provider payload.")

        if series:
            all_dates = [date.fromisoformat(key) for key in series]

            normalize_daily_candles(
                data,
                min(all_dates),
                max(all_dates),
            )

        candles = normalize_daily_candles(
            data,
            start_date,
            end_date,
        )

    except (RuntimeError, ValueError, KeyError, TypeError, AttributeError) as exc:
        logger.warning(
            "Daily research retrieval failed for %s: %s",
            symbol,
            exc,
        )

        return ResearchDataRetrieval(
            candles=[],
            status=ResearchRetrievalStatus.PROVIDER_ERROR,
            source=ResearchDataSource.PROVIDER,
            message=str(exc),
        )

    if USE_CACHE:
        try:
            write_json(cache_file, data)
        except (OSError, TypeError, ValueError) as exc:
            logger.warning(
                "Could not cache daily research data for %s: %s",
                symbol,
                exc,
            )

    if not candles:
        return ResearchDataRetrieval(
            candles=[],
            status=ResearchRetrievalStatus.NO_DATA,
            source=ResearchDataSource.PROVIDER,
            message="No daily candles found in the requested date range.",
        )

    return ResearchDataRetrieval(
        candles=candles,
        status=ResearchRetrievalStatus.SUCCESS,
        source=ResearchDataSource.PROVIDER,
    )
