# =============================================================================
# File: position_analytics.py
# Purpose: Calculates performance metrics for trading positions.
# =============================================================================

from decimal import Decimal
from typing import List

from stonks.journal.execution_side import ExecutionSide
from stonks.journal.position_metrics import PositionMetrics
from stonks.journal.trade_execution import TradeExecution


def calculate_position_metrics(
    position_id: int,
    executions: List[TradeExecution],
) -> PositionMetrics:
    """
    Calculate position metrics using weighted-average cost accounting.

    Assumes executions belong to the requested position, are
    chronologically ordered, and have valid position history.

    Args:
        position_id:
            Identifier of the position being analyzed.

        executions:
            Chronologically ordered executions for the position.

    Returns:
        PositionMetrics:
            Calculated share balance, entry price, remaining
            cost basis, and realized profit or loss.
    """
    open_shares = Decimal("0")
    remaining_cost_basis = Decimal("0")
    remaining_purchase_value = Decimal("0")
    realized_pnl = Decimal("0")

    for execution in executions:
        if execution.side == ExecutionSide.BUY:
            purchase_value = execution.shares * execution.price

            open_shares += execution.shares
            remaining_purchase_value += purchase_value

            remaining_cost_basis += purchase_value + execution.fees

        elif execution.side == ExecutionSide.SELL:
            # Allocate the existing cost basis proportionally
            # to the number of shares being sold.
            cost_of_shares_sold = remaining_cost_basis * execution.shares / open_shares

            purchase_value_sold = remaining_purchase_value * execution.shares / open_shares

            sale_proceeds = execution.shares * execution.price - execution.fees

            realized_pnl += sale_proceeds - cost_of_shares_sold

            remaining_cost_basis -= cost_of_shares_sold
            remaining_purchase_value -= purchase_value_sold
            open_shares -= execution.shares

            if open_shares == 0:
                remaining_cost_basis = Decimal("0")
                remaining_purchase_value = Decimal("0")

    average_entry_price = None

    if open_shares > 0:
        average_entry_price = remaining_purchase_value / open_shares

    return PositionMetrics(
        position_id=position_id,
        open_shares=open_shares,
        average_entry_price=average_entry_price,
        remaining_cost_basis=remaining_cost_basis,
        realized_pnl=realized_pnl,
    )
