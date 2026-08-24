# =============================================================================
# File: market_data.py
# Purpose: Handles market data API requests.
# =============================================================================

import requests

from stonks.config.settings import API_KEY

BASE_URL = "https://www.alphavantage.co/query"

""" NOTE:  Alpha Vantage GLOBAL_QUOTE function returns json format: 
    {
        "Global Quote": {
            "01. symbol": "AAPL",
            "02. open": "296.9700",
            "03. high": "300.5100",
            "04. low": "296.3500",
            "05. price": "298.9700",
            "06. volume": "42243561",
            "07. latest trading day": "2026-05-19",
            "08. previous close": "297.8400",
            "09. change": "1.1300",
            "10. change percent": "0.3794%"
        }
    }
"""


def get_quote(symbol: str):
    """Fetch the latest quote data for a stock symbol."""

    params = {"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": API_KEY}

    response = requests.get(BASE_URL, params=params, timeout=15)

    if response.status_code != 200:
        print(f"Request failed for {symbol}")
        return None

    return response.json()


def get_daily_time_series(symbol: str):
    """Fetch daily historical data for a stock symbol."""

    params = {"function": "TIME_SERIES_DAILY", "symbol": symbol, "apikey": API_KEY}

    response = requests.get(BASE_URL, params=params, timeout=15)

    if response.status_code != 200:
        print(f"Request failed for {symbol}")
        return None

    return response.json()


def get_news_sentiment(symbol: str, limit: int = 10):
    """Fetch recent news and sentiment data for a stock symbol."""

    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": symbol.upper(),
        "sort": "LATEST",
        "limit": limit,
        "apikey": API_KEY,
    }

    response = requests.get(BASE_URL, params=params, timeout=15)

    if response.status_code != 200:
        print(f"News request failed for {symbol.upper()} with status {response.status_code}.")
        return None

    return response.json()
