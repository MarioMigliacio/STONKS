# =============================================================================
# File: position_metrics.py
# Purpose: Represents calculated trading position metrics.
# =============================================================================

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class PositionMetrics:
    """
    Represent calculated performance metrics for a trading position.

    Attributes:
        position_id:
            Database identifier of the analyzed position.

        open_shares:
            Number of shares currently held.

        average_entry_price:
            Weighted-average purchase price of the remaining
            shares, excluding fees. None when no shares are open.

        remaining_cost_basis:
            Cost basis of shares still held, including
            allocated purchase fees.

        realized_pnl:
            Realized profit or loss from sales, after
            allocated purchase fees and selling fees.
    """

    position_id: int
    open_shares: Decimal
    average_entry_price: Optional[Decimal]
    remaining_cost_basis: Decimal
    realized_pnl: Decimal
