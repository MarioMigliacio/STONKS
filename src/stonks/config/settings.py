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
    "TSLA",
    "AMD",
    "NVDA"
]

# Minimum daily volume required for a stock to appear in results.
MIN_VOLUME = 1000
