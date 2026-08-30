# =============================================================================
# File: filters.py
# Purpose: Contains scanner parsing and filtering logic.
# =============================================================================

import logging
import time
from typing import Optional

from stonks.api.market_data import get_quote
from stonks.cache.historical_cache_service import get_historical_data
from stonks.config.settings import MIN_VOLUME, RELATIVE_VOLUME_LOOKBACK_DAYS, WATCHLIST
from stonks.models.quote_data import QuoteData
from stonks.scanner.historical_volume_parser import parse_historical_volumes
from stonks.scanner.relative_volume import (
    calculate_average_volume,
    calculate_relative_volume,
)

logger = logging.getLogger(__name__)


def parse_latest(data: dict) -> Optional[QuoteData]:
    """Parse the latest quote price and volume from API response data."""

    if not data:
        return None

    quote = data.get("Global Quote")

    if not quote:
        return None

    symbol = quote["01. symbol"]
    open_price = float(quote["02. open"])
    price = float(quote["05. price"])
    volume = int(quote["06. volume"])
    latest_trading_day = quote["07. latest trading day"]
    previous_close = float(quote["08. previous close"])
    change_percent = float(quote["10. change percent"].rstrip("%"))
    gap_percent = ((open_price - previous_close) / previous_close) * 100

    return QuoteData(
        symbol=symbol,
        price=price,
        volume=volume,
        change_percent=change_percent,
        gap_percent=gap_percent,
        latest_trading_day=latest_trading_day,
    )


def scan_stocks() -> list[QuoteData]:
    """Scan the watchlist and return stocks matching configured filters."""

    results = []

    logger.info(
        "Starting scanner for %d watchlist symbol(s)",
        len(WATCHLIST),
    )

    for ticker in WATCHLIST:
        logger.info(
            "Scanning %s",
            ticker,
        )

        data = get_quote(ticker)

        # [TODO: remove at a later time] Please be gentle to the API throttling. 25 total per DAY on free account.
        time.sleep(2)

        quote_data = parse_latest(data)

        if not quote_data:
            logger.warning(
                "Skipping %s because quote data could not be parsed",
                ticker,
            )
            continue

        historical_data = get_historical_data(quote_data.symbol)

        if not historical_data:
            logger.warning(
                "Historical data unavailable for %s; relative volume will be 0.0",
                ticker,
            )

        historical_volumes = parse_historical_volumes(historical_data)

        average_volume = calculate_average_volume(
            historical_volumes,
            RELATIVE_VOLUME_LOOKBACK_DAYS,
            quote_data.latest_trading_day,
        )

        relative_volume = calculate_relative_volume(quote_data.volume, average_volume)

        quote_data.average_volume = average_volume
        quote_data.relative_volume = relative_volume

        logger.debug(
            ("%s metrics: price=%.2f, volume=%d, average_volume=%.2f, relative_volume=%.2f, change=%.2f%%, gap=%.2f%%"),
            ticker,
            quote_data.price,
            quote_data.volume,
            quote_data.average_volume,
            quote_data.relative_volume,
            quote_data.change_percent,
            quote_data.gap_percent,
        )

        if quote_data.volume >= MIN_VOLUME:
            logger.debug(
                "%s passed minimum volume filter: %d >= %d",
                ticker,
                quote_data.volume,
                MIN_VOLUME,
            )
            results.append(quote_data)
        else:
            logger.debug(
                "%s failed minimum volume filter: %d < %d",
                ticker,
                quote_data.volume,
                MIN_VOLUME,
            )

    logger.info(
        "Scanner completed with %d matching symbol(s)",
        len(results),
    )

    return results
