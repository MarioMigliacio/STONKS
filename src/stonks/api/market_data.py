# =============================================================================
# File: market_data.py
# Purpose: Handles market data API requests.
# =============================================================================

import requests

from stonks.config.settings import API_KEY

BASE_URL = "https://www.alphavantage.co/query"


def get_quote(symbol):
    """Fetch the latest quote data for a stock symbol."""

    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": API_KEY
    }

    response = requests.get(BASE_URL, params=params)

    if response.status_code != 200:
        print(f"Request failed for {symbol}")
        return None

    return response.json()
