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
    Represents a single executed trade order.

    Attributes:
        order_id:
            Unique identifier for this order.

        position_id:
            Identifier used to group related buy/sell orders into one trade position.

        trade_date:
            Date the order was executed.

        ticker:
            Stock ticker symbol.

        order_type:
            BUY or SELL.

        fill_price:
            Average filled price per share.

        shares:
            Number of shares filled.

        order_total:
            Total dollar value of the order.

        time_issued:
            Time the order was placed or filled.

        notes:
            Optional trade notes.
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