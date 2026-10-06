# =============================================================================
# File: test_account_transaction.py
# Purpose: Pytest file for test_account_transaction.py.
# =============================================================================

from datetime import datetime
from decimal import Decimal

import pytest

from stonks.journal.account_transaction import AccountTransaction
from stonks.journal.account_transaction_type import (
    AccountTransactionType,
)


def create_transaction(
    transaction_type: AccountTransactionType,
    amount: Decimal = Decimal("100.00"),
) -> AccountTransaction:
    """
    Create an account transaction for testing.

    Args:
        transaction_type:
            Account transaction category.

        amount:
            Transaction amount.

    Returns:
        AccountTransaction:
            Constructed transaction instance.
    """
    return AccountTransaction(
        transaction_type=transaction_type,
        occurred_at=datetime(2026, 9, 30, 9, 30),
        amount=amount,
    )


def test_create_transaction() -> None:
    """Verify transaction fields and default values."""

    transaction = create_transaction(AccountTransactionType.DEPOSIT)

    assert transaction.transaction_id is None
    assert transaction.amount == Decimal("100.00")
    assert transaction.notes == ""


def test_deposit_cash_flow() -> None:
    """Verify deposits increase account cash."""

    transaction = create_transaction(AccountTransactionType.DEPOSIT)

    assert transaction.net_cash_flow == Decimal("100.00")


def test_withdrawal_cash_flow() -> None:
    """Verify withdrawals reduce account cash."""

    transaction = create_transaction(AccountTransactionType.WITHDRAWAL)

    assert transaction.net_cash_flow == Decimal("-100.00")


def test_fee_cash_flow() -> None:
    """Verify account-level fees reduce cash."""

    transaction = create_transaction(
        AccountTransactionType.FEE,
        Decimal("40.00"),
    )

    assert transaction.net_cash_flow == Decimal("-40.00")


def test_signed_adjustment() -> None:
    """Verify adjustments preserve their signed amount."""

    transaction = create_transaction(
        AccountTransactionType.ADJUSTMENT,
        Decimal("-15.50"),
    )

    assert transaction.net_cash_flow == Decimal("-15.50")


def test_invalid_transaction_type() -> None:
    """Verify unsupported transaction types are rejected."""

    transaction = create_transaction(AccountTransactionType.DEPOSIT)

    transaction.transaction_type = "INVALID"

    with pytest.raises(ValueError):
        _ = transaction.net_cash_flow
