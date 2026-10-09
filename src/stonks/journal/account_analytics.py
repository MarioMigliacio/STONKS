# =============================================================================
# File: account_analytics.py
# Purpose: Calculates account metrics for non-trading deposits and withdrawals.
# =============================================================================

from decimal import Decimal
from typing import List

from stonks.journal.account_metrics import AccountMetrics
from stonks.journal.account_transaction import AccountTransaction
from stonks.journal.account_transaction_type import AccountTransactionType
from stonks.journal.trade_execution import TradeExecution


def calculate_account_metrics(
    transactions: List[AccountTransaction],
    executions: List[TradeExecution],
) -> AccountMetrics:
    """
    Calculate account contribution metrics from transaction history.

    Only deposits and withdrawals are included in contribution
    calculations. Fees and adjustments are excluded.

    Args:
        transactions:
            Account transactions to analyze.

        executions:
            List of TradeExecutions to draw balance from.

    Returns:
        AccountMetrics:
            Calculated deposits, withdrawals, and net contributions.
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

    return AccountMetrics(
        total_deposits=total_deposits,
        total_withdrawals=total_withdrawals,
        net_contributions=net_contributions,
        cash_balance=cash_balance,
    )
