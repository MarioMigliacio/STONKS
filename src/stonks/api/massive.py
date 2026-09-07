# =============================================================================
# File: massive.py
# Purpose: Retrieves public-float data from the Massive API.
# =============================================================================

import logging
from datetime import date
from typing import Optional

import requests

from stonks.config import settings
from stonks.models.float_data import FloatData

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
