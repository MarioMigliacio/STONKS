import requests

from stonks.config.settings import API_KEY

BASE_URL = "https://www.alphavantage.co/query"


def get_intraday(symbol):
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