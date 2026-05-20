import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("STONKS_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "Missing STONKS_API_KEY. Create a .env file in the project root."
    )

WATCHLIST = [
    "AAPL",
    "TSLA",
    "AMD",
    "NVDA"
]

MIN_VOLUME = 1