# =============================================================================
# File: price_action_summary.py
# Purpose: Represents price-action analysis across a market session and lookbacks.
# =============================================================================

from dataclasses import dataclass

from stonks.models.market_session import MarketSession
from stonks.models.price_action_data import PriceActionData


@dataclass
class PriceActionSummary:
    """
    Represents price-action analysis for a market session.

    Attributes:
        session:
            Market session represented by the analysis.
        session_data:
            Price-action metrics across the entire market session.
        lookbacks:
            Price-action metrics keyed by lookback duration in minutes.
    """

    session: MarketSession
    session_data: PriceActionData
    lookbacks: dict[int, PriceActionData]
