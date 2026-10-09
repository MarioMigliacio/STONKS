# =============================================================================
# File: position_analytics.py
# Purpose: Calculates performance metrics for trading positions.
# =============================================================================

from decimal import Decimal
from typing import List

from stonks.journal.execution_side import ExecutionSide
from stonks.journal.position_metrics import PositionMetrics
from stonks.journal.position_status import PositionStatus
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
    total_cost_of_shares_sold = Decimal("0")
    has_executions = False
    opened_at = None
    closed_at = None

    for execution in executions:
        has_executions = True
        if execution.side == ExecutionSide.BUY:
            if opened_at is None:
                opened_at = execution.executed_at

            purchase_value = execution.shares * execution.price

            open_shares += execution.shares
            remaining_purchase_value += purchase_value

            remaining_cost_basis += purchase_value + execution.fees

        elif execution.side == ExecutionSide.SELL:
            # Allocate the existing cost basis proportionally
            # to the number of shares being sold.
            cost_of_shares_sold = remaining_cost_basis * execution.shares / open_shares

            total_cost_of_shares_sold += cost_of_shares_sold

            purchase_value_sold = remaining_purchase_value * execution.shares / open_shares

            sale_proceeds = execution.shares * execution.price - execution.fees

            realized_pnl += sale_proceeds - cost_of_shares_sold

            remaining_cost_basis -= cost_of_shares_sold
            remaining_purchase_value -= purchase_value_sold
            open_shares -= execution.shares

            if open_shares == 0:
                remaining_cost_basis = Decimal("0")
                remaining_purchase_value = Decimal("0")
                closed_at = execution.executed_at

    average_entry_price = None

    if open_shares > 0:
        average_entry_price = remaining_purchase_value / open_shares

    if not has_executions:
        status = PositionStatus.DRAFT
    elif open_shares > 0:
        status = PositionStatus.OPEN
    else:
        status = PositionStatus.CLOSED

    realized_return_pct = None

    if total_cost_of_shares_sold > 0:
        realized_return_pct = realized_pnl / total_cost_of_shares_sold * Decimal("100")

    holding_duration = None

    if opened_at is not None and closed_at is not None:
        holding_duration = closed_at - opened_at

    return PositionMetrics(
        position_id=position_id,
        open_shares=open_shares,
        average_entry_price=average_entry_price,
        remaining_cost_basis=remaining_cost_basis,
        realized_pnl=realized_pnl,
        status=status,
        realized_return_pct=realized_return_pct,
        opened_at=opened_at,
        closed_at=closed_at,
        holding_duration=holding_duration,
    )
