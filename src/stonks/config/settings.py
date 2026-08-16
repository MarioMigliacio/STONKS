# =============================================================================
# File: settings.py
# Purpose: Central configuration values for STONKS.
# =============================================================================

import os
from dotenv import load_dotenv

# Load environment variables from the local .env file.
load_dotenv()

API_KEY = os.getenv("STONKS_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "Missing STONKS_API_KEY. Create a .env file in the project root."
    )

# Initial hardcoded watchlist used by the scanner.
WATCHLIST = [
    "AAPL",
    "SPCX"#,
    #"MSFT",
    #"AMD",
    #"NVDA"
]

# Minimum daily volume required for a stock to appear in results.
MIN_VOLUME = 1000

# Cache behavior
USE_CACHE = True

# Safety switch:
# False = never call external APIs; cache-only mode.
# True  = call API only when cache is missing/stale.
ALLOW_API_CALLS = True

# historic data lookback constant for 30 day average.
RELATIVE_VOLUME_LOOKBACK_DAYS = 30

# CIA breaking news thresholds
# 0 - 60 minutes    🔥 Breaking
# 1 - 4 hours          Fresh
# 4 - 24 hours         Recent
# 24+ hours            Stale
CIA_BREAKING_NEWS_MINUTES = 60
CIA_FRESH_NEWS_HOURS = 4
CIA_RECENT_NEWS_HOURS = 24