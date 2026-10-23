# =============================================================================
# File: account_analytics.py
# Purpose: Calculates account contributions, cash flow, and realized
#          profitability from journal transaction and execution history.
# =============================================================================

from decimal import Decimal
from typing import List, Optional

from stonks.journal.analytics.account_metrics import AccountMetrics
from stonks.journal.analytics.position_metrics import PositionMetrics
from stonks.journal.models.account_transaction import AccountTransaction
from stonks.journal.models.account_transaction_type import AccountTransactionType
from stonks.journal.models.opening_cash_balance import OpeningCashBalance
from stonks.journal.models.trade_execution import TradeExecution


def calculate_account_metrics(
    transactions: List[AccountTransaction],
    executions: List[TradeExecution],
    positions: List[PositionMetrics],
    opening_cash: Optional[OpeningCashBalance] = None,
) -> AccountMetrics:
    """
    Calculate account cash flow and realized profitability metrics.

    A dated opening cash snapshot replaces the cash ledger history preceding
    its effective timestamp; it is not a deposit or realized trading profit.
    Transactions and executions at the exact effective timestamp are included.

    Contribution and realized-profit metrics intentionally continue to cover
    all supplied records, including records preceding the snapshot. The
    snapshot only changes reconstructed cash and equity at cost basis.

    With no opening snapshot, historical behavior is preserved: the cash
    calculation starts at zero and includes all supplied cash movements.
    This zero starting point is an assumption, not a verified account balance.
    No unrealized gains or market-value account equity are calculated.

    Args:
        transactions:
            Account transactions to analyze.

        executions:
            Trade executions supplying cash movements.

        positions:
            Previously calculated position metrics.

        opening_cash:
            Optional opening cash snapshot and UTC-aware effective time.

    Returns:
        AccountMetrics:
            Calculated contributions, ledger cash, profitability, cost basis,
            and equity at cost basis.
    """
    total_deposits = Decimal("0")
    total_withdrawals = Decimal("0")
    cash_balance = opening_cash.amount if opening_cash is not None else Decimal("0")
    boundary = opening_cash.effective_at if opening_cash is not None else None

    for transaction in transactions:
        if boundary is None or transaction.occurred_at >= boundary:
            cash_balance += transaction.net_cash_flow

        if transaction.transaction_type == AccountTransactionType.DEPOSIT:
            total_deposits += transaction.amount
        elif transaction.transaction_type == AccountTransactionType.WITHDRAWAL:
            total_withdrawals += transaction.amount

    for execution in executions:
        if boundary is None or execution.executed_at >= boundary:
            cash_balance += execution.net_cash_flow

    net_contributions = total_deposits - total_withdrawals

    realized_trading_pnl = sum(
        (position.realized_pnl for position in positions),
        Decimal("0"),
    )

    account_fees = sum(
        (
            transaction.amount
            for transaction in transactions
            if transaction.transaction_type == AccountTransactionType.FEE
        ),
        Decimal("0"),
    )

    net_realized_pnl = realized_trading_pnl - account_fees

    open_position_cost_basis = sum(
        (position.remaining_cost_basis for position in positions),
        Decimal("0"),
    )

    equity_at_cost_basis = cash_balance + open_position_cost_basis

    return AccountMetrics(
        total_deposits=total_deposits,
        total_withdrawals=total_withdrawals,
        net_contributions=net_contributions,
        cash_balance=cash_balance,
        realized_trading_pnl=realized_trading_pnl,
        account_fees=account_fees,
        net_realized_pnl=net_realized_pnl,
        open_position_cost_basis=open_position_cost_basis,
        equity_at_cost_basis=equity_at_cost_basis,
    )
