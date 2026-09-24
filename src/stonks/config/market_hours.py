# =============================================================================
# File: market_hours.py
# Purpose: Defines U.S. equity market timezone and trading-session boundaries.
# =============================================================================

from datetime import time
from zoneinfo import ZoneInfo

MARKET_TIMEZONE = ZoneInfo("America/New_York")

PRE_MARKET_OPEN = time(4, 0)

REGULAR_MARKET_OPEN = time(9, 30)
REGULAR_MARKET_CLOSE = time(16, 0)

AFTER_HOURS_CLOSE = time(20, 0)
