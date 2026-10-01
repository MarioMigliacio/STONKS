# =============================================================================
# File: trade_order.py
# Purpose: Defines the trade order model used by the STONKS journal subsystem.
#
# Notes:
# - A TradeOrder represents one filled buy or sell order.
# - Multiple TradeOrder records may belong to the same position_id.
# - Position-level metrics can be calculated later by grouping orders together.
# =============================================================================

from dataclasses import dataclass


@dataclass
class TradeOrder:
    """
    Represents a single executed buy or sell order within a trading position.

    Multiple orders may share a position_id, allowing a position to
    contain partial entries, partial exits, and multiple executions.

    Attributes:
        order_id:
            Unique integer identifier for this executed order.

        position_id:
            Integer identifier grouping orders belonging to the
            same trading position.

        trade_date:
            Execution date, stored as a string in the journal's
            existing date format.

        ticker:
            Stock ticker symbol associated with the order.

        order_type:
            Order direction, expected to be "BUY" or "SELL".

        fill_price:
            Average execution price per share, in dollars.

        shares:
            Number of shares executed in this order.

        order_total:
            Total dollar value of the executed order.

        time_issued:
            Time the order was placed or executed, stored as a
            string in the journal's existing time format.

        notes:
            Optional user-provided notes about the order.
            Defaults to an empty string.
    """

    order_id: int
    position_id: int
    trade_date: str
    ticker: str
    order_type: str
    fill_price: float
    shares: int
    order_total: float
    time_issued: str
    notes: str = ""
