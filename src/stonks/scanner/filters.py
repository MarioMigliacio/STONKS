import time

from stonks.api.market_data import get_intraday
from stonks.models.stock import Stock
from stonks.config.settings import WATCHLIST
from stonks.config.settings import MIN_VOLUME

def parse_latest(data):
    if not data:
        return None

    quote = data.get("Global Quote")

    if not quote:
        return None

    price = float(quote["05. price"])
    volume = int(quote["06. volume"])

    return price, volume

def scan_stocks():
    results = []

    for ticker in WATCHLIST:
        print(f"Scanning {ticker}...")

        data = get_intraday(ticker)

        # Please be gentle to the API throttling. 12 sec / min to 5 requests max per min as API limits on free tier. 25 total per DAY.
        time.sleep(12)

        parsed = parse_latest(data)

        if not parsed:
            continue

        price, volume = parsed
        print(f"{ticker} | Price={price} | Volume={volume}")

        if volume >= MIN_VOLUME:
            stock = Stock(ticker, price, volume)
            results.append(stock)

    return results