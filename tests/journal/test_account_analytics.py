# =============================================================================
# File: test_account_analytics.py
# Purpose: Pytest file for test_account_analytics.py.
# =============================================================================

from datetime import datetime, timezone
from decimal import Decimal

from stonks.journal.account_analytics import (
    calculate_account_metrics,
)
from stonks.journal.account_transaction import AccountTransaction
from stonks.journal.account_transaction_type import AccountTransactionType
from stonks.journal.execution_side import ExecutionSide
from stonks.journal.trade_execution import TradeExecution


def make_transaction(
    transaction_type: AccountTransactionType,
    amount: str,
) -> AccountTransaction:
    """
    Create an account transaction for analytics testing.

    Args:
        transaction_type:
            Type of account transaction.

        amount:
            Transaction amount represented as a decimal string.

    Returns:
        AccountTransaction:
            Transaction populated with test values.
    """
    return AccountTransaction(
        transaction_type=transaction_type,
        amount=Decimal(amount),
        occurred_at=datetime(2026, 10, 8, 14, 30, tzinfo=timezone.utc),
    )


def make_execution(
    side: ExecutionSide,
    shares: str,
    price: str,
    fees: str = "0",
) -> TradeExecution:
    """
    Create a trade execution for account analytics testing.

    Args:
        side:
            BUY or SELL execution side.
        shares:
            Number of shares executed.
        price:
            Execution price per share.
        fees:
            Execution fees.

    Returns:
        TradeExecution:
            Execution populated with test values.
    """
    return TradeExecution(
        position_id=1,
        side=side,
        executed_at=datetime(2026, 10, 8, 14, 30, tzinfo=timezone.utc),
        shares=Decimal(shares),
        price=Decimal(price),
        fees=Decimal(fees),
    )


def test_empty_account_contributions() -> None:
    """Verify an account without transactions has zero contributions."""

    metrics = calculate_account_metrics([], [])

    assert metrics.total_deposits == Decimal("0")
    assert metrics.total_withdrawals == Decimal("0")
    assert metrics.net_contributions == Decimal("0")
    assert metrics.cash_balance == Decimal("0")


def test_multiple_deposits() -> None:
    """Verify multiple deposits accumulate correctly."""

    transactions = [
        make_transaction(AccountTransactionType.DEPOSIT, "1000"),
        make_transaction(AccountTransactionType.DEPOSIT, "250.50"),
    ]

    metrics = calculate_account_metrics(transactions, [])

    assert metrics.total_deposits == Decimal("1250.50")
    assert metrics.total_withdrawals == Decimal("0")
    assert metrics.net_contributions == Decimal("1250.50")
    assert metrics.cash_balance == Decimal("1250.50")


def test_deposits_and_withdrawals() -> None:
    """Verify withdrawals reduce net contributions."""

    transactions = [
        make_transaction(AccountTransactionType.DEPOSIT, "1000"),
        make_transaction(AccountTransactionType.WITHDRAWAL, "300"),
        make_transaction(AccountTransactionType.DEPOSIT, "200"),
    ]

    metrics = calculate_account_metrics(transactions, [])

    assert metrics.total_deposits == Decimal("1200")
    assert metrics.total_withdrawals == Decimal("300")
    assert metrics.net_contributions == Decimal("900")
    assert metrics.cash_balance == Decimal("900")


def test_fees_and_adjustments_excluded() -> None:
    """Verify non-contribution transactions do not affect contributions."""

    transactions = [
        make_transaction(AccountTransactionType.DEPOSIT, "1000"),
        make_transaction(AccountTransactionType.FEE, "5"),
        make_transaction(AccountTransactionType.ADJUSTMENT, "25"),
    ]

    metrics = calculate_account_metrics(transactions, [])

    assert metrics.total_deposits == Decimal("1000")
    assert metrics.total_withdrawals == Decimal("0")
    assert metrics.net_contributions == Decimal("1000")
    assert metrics.cash_balance == Decimal("1020")


def test_purchase_reduces_cash_balance() -> None:
    """Verify purchases reduce available account cash."""

    transactions = [
        make_transaction(AccountTransactionType.DEPOSIT, "1000"),
    ]

    executions = [
        make_execution(ExecutionSide.BUY, "10", "25"),
    ]

    metrics = calculate_account_metrics(transactions, executions)

    assert metrics.cash_balance == Decimal("750")
    assert metrics.net_contributions == Decimal("1000")


def test_sale_increases_cash_balance() -> None:
    """Verify sales return proceeds to the account."""

    transactions = [
        make_transaction(AccountTransactionType.DEPOSIT, "1000"),
    ]

    executions = [
        make_execution(ExecutionSide.BUY, "10", "25"),
        make_execution(ExecutionSide.SELL, "5", "30"),
    ]

    metrics = calculate_account_metrics(transactions, executions)

    assert metrics.cash_balance == Decimal("900")


def test_execution_fees_reduce_cash_balance() -> None:
    """Verify execution fees are applied exactly once."""

    transactions = [
        make_transaction(AccountTransactionType.DEPOSIT, "1000"),
    ]

    executions = [
        make_execution(ExecutionSide.BUY, "10", "25", fees="1.50"),
        make_execution(ExecutionSide.SELL, "5", "30", fees="2.50"),
    ]

    metrics = calculate_account_metrics(transactions, executions)

    assert metrics.cash_balance == Decimal("896.00")


def test_account_fees_reduce_cash_balance() -> None:
    """Verify standalone account fees reduce cash."""

    transactions = [
        make_transaction(AccountTransactionType.DEPOSIT, "1000"),
        make_transaction(AccountTransactionType.FEE, "5"),
    ]

    metrics = calculate_account_metrics(transactions, [])

    assert metrics.cash_balance == Decimal("995")
    assert metrics.net_contributions == Decimal("1000")


def test_adjustments_modify_cash_balance() -> None:
    """Verify signed adjustments modify cash without changing contributions."""

    transactions = [
        make_transaction(AccountTransactionType.DEPOSIT, "1000"),
        make_transaction(AccountTransactionType.ADJUSTMENT, "25"),
        make_transaction(AccountTransactionType.ADJUSTMENT, "-10"),
    ]

    metrics = calculate_account_metrics(transactions, [])

    assert metrics.cash_balance == Decimal("1015")
    assert metrics.net_contributions == Decimal("1000")
