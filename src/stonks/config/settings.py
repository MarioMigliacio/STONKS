# =============================================================================
# File: settings.py
# Purpose: Central configuration values for STONKS.
# =============================================================================

import os

from dotenv import load_dotenv

# Load environment variables from the local .env file.
load_dotenv()

API_KEY = os.getenv("STONKS_API_KEY")

# Initial hardcoded watchlist used by the scanner.
WATCHLIST = ["AAPL", "SPCX"]

# Minimum daily volume required for a stock to appear in results.
MIN_VOLUME = 1000

# Cache behavior
USE_CACHE = True

# Safety switch.
ALLOW_API_CALLS = True

# Historical data lookback used for relative volume calculations.
RELATIVE_VOLUME_LOOKBACK_DAYS = 30


# =============================================================================
# C.I.A. Configuration
# =============================================================================

# CIA news freshness thresholds.
# 0 - 60 minutes    Breaking
# 1 - 4 hours       Fresh
# 4 - 24 hours      Recent
# 24+ hours         Stale
CIA_BREAKING_NEWS_MINUTES = 60
CIA_FRESH_NEWS_HOURS = 4
CIA_RECENT_NEWS_HOURS = 24

# CIA sentiment classification thresholds.
CIA_BULLISH_SENTIMENT_THRESHOLD = 0.35
CIA_SOMEWHAT_BULLISH_SENTIMENT_THRESHOLD = 0.15
CIA_SOMEWHAT_BEARISH_SENTIMENT_THRESHOLD = -0.15
CIA_BEARISH_SENTIMENT_THRESHOLD = -0.35
