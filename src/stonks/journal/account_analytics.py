# =============================================================================
# File: account_analytics.py
# Purpose: Calculates account contributions, cash flow, and realized
#          profitability from journal transaction and execution history.
# =============================================================================

from decimal import Decimal
from typing import List

from stonks.journal.account_metrics import AccountMetrics
from stonks.journal.account_transaction import AccountTransaction
from stonks.journal.account_transaction_type import AccountTransactionType
from stonks.journal.position_metrics import PositionMetrics
from stonks.journal.trade_execution import TradeExecution


def calculate_account_metrics(
    transactions: List[AccountTransaction],
    executions: List[TradeExecution],
    positions: List[PositionMetrics],
) -> AccountMetrics:
    """
    Calculate account cash flow and realized profitability metrics.

    Aggregates account transactions, trade execution cash flows,
    and previously calculated position metrics.

    Deposits and withdrawals determine net contributions.
    Transaction and execution cash flows determine the cash balance.
    Position metrics determine realized trading profit or loss.

    Standalone account fees are deducted from realized trading
    profit or loss without double-counting execution fees.

    Cash adjustments affect the cash balance but are excluded
    from realized trading profitability.

    The calculation assumes complete account history and an
    opening cash balance of zero. It does not calculate
    unrealized gains, losses, or market-value account equity.

    Args:
        transactions:
            Account transactions to analyze, including deposits,
            withdrawals, fees, and adjustments.

        executions:
            Trade executions used to reconstruct account cash
            movements.

        positions:
            Previously calculated position metrics used to
            aggregate realized trading profit or loss.

    Returns:
        AccountMetrics:
            Calculated account contributions, cash balance,
            realized trading profit or loss, account fees,
            and net realized profit or loss.
    """
    total_deposits = Decimal("0")
    total_withdrawals = Decimal("0")
    cash_balance = Decimal("0")

    for transaction in transactions:
        cash_balance += transaction.net_cash_flow

        if transaction.transaction_type == AccountTransactionType.DEPOSIT:
            total_deposits += transaction.amount

        elif transaction.transaction_type == AccountTransactionType.WITHDRAWAL:
            total_withdrawals += transaction.amount

    for execution in executions:
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

    return AccountMetrics(
        total_deposits=total_deposits,
        total_withdrawals=total_withdrawals,
        net_contributions=net_contributions,
        cash_balance=cash_balance,
        realized_trading_pnl=realized_trading_pnl,
        account_fees=account_fees,
        net_realized_pnl=net_realized_pnl,
    )
