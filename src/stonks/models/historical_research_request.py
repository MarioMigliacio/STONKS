# =============================================================================
# File: historical_research_request.py
# Purpose: Defines user-selected parameters for historical research.
# =============================================================================

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from stonks.models.market_session import MarketSession
from stonks.models.research_interval import ResearchInterval


@dataclass(frozen=True)
class HistoricalResearchRequest:
    """
    Represents a historical market-data research request.

    Attributes:
        symbol:
            Stock ticker being researched.

        start_date:
            First requested trading date, inclusive.

        end_date:
            Last requested trading date, inclusive.

        interval:
            Candle interval used for chart presentation.

        session:
            Market session for intraday research, if applicable.

        window_start:
            Inclusive analysis-window start, when specified.

        window_end:
            Exclusive analysis-window end, when specified.

        force_refresh:
            Whether to bypass cached data and request fresh data.
    """

    symbol: str
    start_date: date
    end_date: date
    interval: ResearchInterval
    session: Optional[MarketSession] = None
    window_start: Optional[datetime] = None
    window_end: Optional[datetime] = None
    force_refresh: bool = False

    def __post_init__(self) -> None:
        """Validate research parameters and normalize the ticker."""
        symbol = self.symbol.strip().upper()

        if not symbol:
            raise ValueError("Research symbol cannot be empty.")

        object.__setattr__(self, "symbol", symbol)

        if self.start_date > self.end_date:
            raise ValueError("Start date must not exceed end date.")

        if (self.window_start is None) != (self.window_end is None):
            raise ValueError("Both analysis-window boundaries are required.")

        if self.window_start is not None and self.window_end is not None:
            for boundary in (self.window_start, self.window_end):
                if boundary.tzinfo is None or boundary.utcoffset() is None:
                    raise ValueError("Analysis-window boundaries must be timezone-aware.")

            if self.window_start >= self.window_end:
                raise ValueError("Analysis-window start must precede end.")

        intraday_intervals = {
            ResearchInterval.ONE_MINUTE,
            ResearchInterval.FIVE_MINUTES,
            ResearchInterval.TEN_MINUTES,
            ResearchInterval.FIFTEEN_MINUTES,
            ResearchInterval.THIRTY_MINUTES,
            ResearchInterval.SIXTY_MINUTES,
        }

        if self.interval in intraday_intervals:
            if self.start_date != self.end_date:
                raise ValueError("Intraday research requires a single trading date.")
        elif self.session is not None:
            raise ValueError("Market-session selection applies only to intraday research.")
