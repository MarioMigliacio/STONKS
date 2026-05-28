# =============================================================================
# File: filters.py
# Purpose: Contains scanner parsing and filtering logic.
# =============================================================================

import time

from stonks.api.market_data import get_quote
from stonks.models.stock import Stock
from stonks.models.quote_data import QuoteData
from stonks.config.settings import WATCHLIST
from stonks.config.settings import MIN_VOLUME

def parse_latest(data):
    """Parse the latest quote price and volume from API response data."""

    if not data:
        return None

    quote = data.get("Global Quote")

    if not quote:
        return None

    price = float(quote["05. price"])
    volume = int(quote["06. volume"])

    change_percent_text = quote["10. change percent"]
    change_percent = float(change_percent_text.replace("%", ""))

    return QuoteData(
    symbol=quote["01. symbol"],
    price=price,
    volume=volume,
    change_percent=change_percent
)

def scan_stocks():
    """Scan the watchlist and return stocks matching configured filters."""

    results = []

    for ticker in WATCHLIST:
        print(f"Scanning {ticker}...")

        data = get_quote(ticker)

        # Please be gentle to the API throttling. 12 sec / min to 5 requests max per min as API limits on free tier. 25 total per DAY.
        time.sleep(12)

        parsed = parse_latest(data)

        if not parsed:
            continue

        quote_data = parsed

        print(
            f"{ticker} | "
            f"Price={quote_data.price} | "
            f"Volume={quote_data.volume:,} | "
            f"Change={quote_data.change_percent}%"
        )

        if quote_data.volume >= MIN_VOLUME:
            stock = Stock(ticker, quote_data.price, quote_data.volume, quote_data.change_percent)
            results.append(stock)

    return results
