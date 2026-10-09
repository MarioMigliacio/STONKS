# =============================================================================
# File: position_metrics.py
# Purpose: Represents calculated trading position metrics.
# =============================================================================

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from stonks.journal.position_status import PositionStatus


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

        status:
            Lifecycle status of the position.

        realized_return_pct:
            Realized profit or loss as a percentage of the
            cost basis allocated to sold shares. None when
            no shares have been sold.

        opened_at:
            Timestamp of the first BUY execution.
            None for draft positions.

        closed_at:
            Timestamp of the final SELL execution that closed
            the position. None for open or draft positions.

        holding_duration:
            Elapsed time between opening and closing the
            position. None while the position remains open.
    """

    position_id: int
    open_shares: Decimal
    average_entry_price: Optional[Decimal]
    remaining_cost_basis: Decimal
    realized_pnl: Decimal
    status: PositionStatus
    realized_return_pct: Optional[Decimal]
    opened_at: Optional[datetime]
    closed_at: Optional[datetime]
    holding_duration: Optional[timedelta]
