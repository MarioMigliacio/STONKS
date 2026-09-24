# =============================================================================
# File: market_session.py
# Purpose: Defines supported U.S. market trading sessions.
# =============================================================================

from enum import Enum


class MarketSession(Enum):
    """Represents a supported U.S. market trading session."""

    PRE_MARKET = "pre_market"
    REGULAR = "regular"
    AFTER_HOURS = "after_hours"
