# =============================================================================
# File: research_interval.py
# Purpose: Defines candle intervals supported by historical research.
# =============================================================================

from enum import Enum


class ResearchInterval(Enum):
    """Represents a candle interval available in the research workspace."""

    ONE_MINUTE = "1min"
    FIVE_MINUTES = "5min"
    TEN_MINUTES = "10min"
    FIFTEEN_MINUTES = "15min"
    THIRTY_MINUTES = "30min"
    SIXTY_MINUTES = "60min"

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
