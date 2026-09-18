# =============================================================================
# File: massive.py
# Purpose: Retrieves market data from the Massive API.
# =============================================================================

import logging
from datetime import date, datetime, timezone
from typing import Optional

import requests

from stonks.config import settings
from stonks.models.candle_data import CandleData
from stonks.models.float_data import FloatData
from stonks.models.timeframe import Timeframe

logger = logging.getLogger(__name__)

BASE_URL = "https://api.massive.com"
FLOAT_ENDPOINT = "/stocks/vX/float"


def require_api_key() -> str:
    """Return the Massive API key required for float-data requests."""

    if not settings.MASSIVE_API_KEY:
        raise RuntimeError("Missing STONKS_MASSIVE_API_KEY. Configure a Massive API key to use float data.")

    return settings.MASSIVE_API_KEY


def get_float(symbol: str) -> Optional[FloatData]:
    """Retrieve reported public-float data for a stock."""

    symbol = symbol.upper()

    logger.debug(
        "Requesting float data for %s",
        symbol,
    )

    headers = {
        "Authorization": f"Bearer {require_api_key()}",
    }

    params = {
        "ticker": symbol,
    }

    response = requests.get(
        f"{BASE_URL}{FLOAT_ENDPOINT}",
        headers=headers,
        params=params,
        timeout=15,
    )

    if response.status_code != 200:
        logger.error(
            "Float request failed for %s with status %d",
            symbol,
            response.status_code,
        )
        return None

    data = response.json()
    results = data.get("results", [])

    if not results:
        logger.warning(
            "No float data returned for %s",
            symbol,
        )
        return None

    result = results[0]

    ticker = result.get("ticker")
    free_float = result.get("free_float")
    free_float_percent = result.get("free_float_percent")
    effective_date_text = result.get("effective_date")

    if not ticker or free_float is None or free_float_percent is None or not effective_date_text:
        logger.warning(
            "Incomplete float data returned for %s",
            symbol,
        )
        return None

    effective_date = date.fromisoformat(effective_date_text)

    logger.debug(
        "Float data retrieved for %s",
        symbol,
    )

    return FloatData(
        symbol=ticker,
        float_shares=free_float,
        float_percent=free_float_percent,
        effective_date=effective_date,
        source="Massive",
    )


def _get_aggregate_interval(timeframe: Timeframe) -> tuple[int, str]:
    """Convert a STONKS timeframe to a Massive aggregate interval."""

    intervals = {
        Timeframe.ONE_MINUTE: (1, "minute"),
        Timeframe.FIVE_MINUTES: (5, "minute"),
        Timeframe.FIFTEEN_MINUTES: (15, "minute"),
        Timeframe.THIRTY_MINUTES: (30, "minute"),
        Timeframe.SIXTY_MINUTES: (60, "minute"),
        Timeframe.DAILY: (1, "day"),
    }

    return intervals[timeframe]


def get_aggregate_bars(
    symbol: str,
    timeframe: Timeframe,
    start_date: date,
    end_date: date,
) -> list[CandleData]:
    """Retrieve historical OHLCV aggregate bars for a stock."""

    symbol = symbol.upper()
    multiplier, timespan = _get_aggregate_interval(timeframe)

    logger.debug(
        "Requesting %s aggregate bars for %s from %s to %s",
        timeframe.value,
        symbol,
        start_date,
        end_date,
    )

    headers = {
        "Authorization": f"Bearer {require_api_key()}",
    }

    params = {
        "adjusted": "true",
        "sort": "asc",
        "limit": 50000,
    }

    endpoint = f"/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{start_date.isoformat()}/{end_date.isoformat()}"

    response = requests.get(
        f"{BASE_URL}{endpoint}",
        headers=headers,
        params=params,
        timeout=15,
    )

    if response.status_code != 200:
        logger.error(
            "Aggregate bars request failed for %s with status %d",
            symbol,
            response.status_code,
        )
        return []

    data = response.json()
    results = data.get("results", [])

    if not results:
        logger.warning(
            "No aggregate bars returned for %s",
            symbol,
        )
        return []

    candles = [
        CandleData(
            timestamp=datetime.fromtimestamp(
                result["t"] / 1000,
                tz=timezone.utc,
            ),
            open_price=float(result["o"]),
            high_price=float(result["h"]),
            low_price=float(result["l"]),
            close_price=float(result["c"]),
            volume=int(result["v"]),
        )
        for result in results
    ]

    logger.debug(
        "Retrieved %d aggregate bars for %s",
        len(candles),
        symbol,
    )

    return candles
