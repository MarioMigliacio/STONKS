# =============================================================================
# File: filters.py
# Purpose: Contains scanner parsing and filtering logic.
# =============================================================================

import time

from stonks.api.market_data import get_quote
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

    open_price = float(quote["02. open"])
    price = float(quote["05. price"])
    volume = int(quote["06. volume"])
    previous_close = float(quote["08. previous close"])

    change_percent_text = quote["10. change percent"]
    change_percent = float(change_percent_text.replace("%", ""))
    gap_percent = ((open_price - previous_close) / previous_close) * 100

    return QuoteData(
    symbol=quote["01. symbol"],
    price=price,
    volume=volume,
    change_percent=change_percent,
    gap_percent=gap_percent
)

def scan_stocks():
    """Scan the watchlist and return stocks matching configured filters."""

    results = []

    for ticker in WATCHLIST:
        print(f"Scanning {ticker}...")

        data = get_quote(ticker)

        # Please be gentle to the API throttling. 25 total per DAY on free account.
        time.sleep(2)

        parsed = parse_latest(data)

        if not parsed:
            continue

        quote_data = parsed

        print(
            f"{ticker} | "
            f"Price={quote_data.price} | "
            f"Volume={quote_data.volume:,} | "
            f"Change={quote_data.change_percent}% | "
            f"Gap={quote_data.gap_percent}%"
        )

        if quote_data.volume >= MIN_VOLUME:
            results.append(quote_data)

    return results