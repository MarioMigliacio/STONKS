# =============================================================================
# File: test_journal_service_accounts.py
# Purpose: Pytest file for test_journal_service_accounts.py.
# =============================================================================

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from stonks.journal.account_transaction import AccountTransaction
from stonks.journal.account_transaction_type import (
    AccountTransactionType,
)


def make_account_transaction(
    transaction_type: AccountTransactionType,
    amount: Decimal,
) -> AccountTransaction:
    """Construct an account transaction for testing."""

    return AccountTransaction(
        transaction_type=transaction_type,
        occurred_at=datetime(
            2026,
            9,
            30,
            13,
            30,
            tzinfo=timezone.utc,
        ),
        amount=amount,
    )


@pytest.mark.parametrize(
    "transaction_type, amount, expected_cash_flow",
    [
        (
            AccountTransactionType.DEPOSIT,
            Decimal("100.00"),
            Decimal("100.00"),
        ),
        (
            AccountTransactionType.WITHDRAWAL,
            Decimal("25.50"),
            Decimal("-25.50"),
        ),
        (
            AccountTransactionType.FEE,
            Decimal("2.25"),
            Decimal("-2.25"),
        ),
        (
            AccountTransactionType.ADJUSTMENT,
            Decimal("-12.75"),
            Decimal("-12.75"),
        ),
        (
            AccountTransactionType.ADJUSTMENT,
            Decimal("5.25"),
            Decimal("5.25"),
        ),
    ],
)
def test_create_account_transaction(
    journal,
    transaction_type: AccountTransactionType,
    amount: Decimal,
    expected_cash_flow: Decimal,
) -> None:
    """Verify supported account transactions persist."""

    service, repository, _ = journal

    transaction = make_account_transaction(
        transaction_type,
        amount,
    )

    transaction_id = service.create_account_transaction(transaction)

    loaded = repository.get_account_transaction(transaction_id)

    assert loaded is not None
    assert loaded.transaction_type == transaction_type
    assert loaded.amount == amount
    assert loaded.net_cash_flow == expected_cash_flow


@pytest.mark.parametrize(
    "transaction_type, amount",
    [
        (
            AccountTransactionType.DEPOSIT,
            Decimal("-100"),
        ),
        (
            AccountTransactionType.WITHDRAWAL,
            Decimal("0"),
        ),
        (
            AccountTransactionType.FEE,
            Decimal("-1"),
        ),
        (
            AccountTransactionType.DEPOSIT,
            Decimal("NaN"),
        ),
        (
            AccountTransactionType.ADJUSTMENT,
            Decimal("Infinity"),
        ),
    ],
)
def test_invalid_account_transaction(
    journal,
    transaction_type: AccountTransactionType,
    amount: Decimal,
) -> None:
    """Verify invalid transactions are never persisted."""

    service, repository, _ = journal

    transaction = make_account_transaction(
        transaction_type,
        amount,
    )

    with pytest.raises(ValueError):
        service.create_account_transaction(transaction)

    assert repository.get_account_transactions() == []


def test_account_transaction_utc_normalization(
    journal,
) -> None:
    """Verify account timestamps are normalized to UTC."""

    service, repository, _ = journal

    transaction = make_account_transaction(
        AccountTransactionType.DEPOSIT,
        Decimal("100"),
    )

    transaction.occurred_at = datetime(
        2026,
        9,
        30,
        6,
        30,
        tzinfo=timezone(timedelta(hours=-7)),
    )

    transaction_id = service.create_account_transaction(transaction)

    loaded = repository.get_account_transaction(transaction_id)

    assert loaded is not None
    assert loaded.occurred_at == datetime(
        2026,
        9,
        30,
        13,
        30,
        tzinfo=timezone.utc,
    )
    assert loaded.occurred_at.utcoffset() == timedelta(0)


def test_update_account_transaction(journal) -> None:
    """Verify existing transactions can be corrected."""

    service, repository, _ = journal

    transaction_id = service.create_account_transaction(
        make_account_transaction(
            AccountTransactionType.DEPOSIT,
            Decimal("100"),
        )
    )

    transaction = repository.get_account_transaction(transaction_id)

    assert transaction is not None

    transaction.amount = Decimal("150.75")
    transaction.notes = "Corrected deposit"

    assert service.update_account_transaction(transaction) is True

    loaded = repository.get_account_transaction(transaction_id)

    assert loaded is not None
    assert loaded.amount == Decimal("150.75")
    assert loaded.notes == "Corrected deposit"


def test_invalid_account_update_preserves_record(
    journal,
) -> None:
    """Verify rejected updates leave stored data unchanged."""

    service, repository, _ = journal

    transaction_id = service.create_account_transaction(
        make_account_transaction(
            AccountTransactionType.DEPOSIT,
            Decimal("100"),
        )
    )

    transaction = repository.get_account_transaction(transaction_id)

    assert transaction is not None

    transaction.amount = Decimal("-50")

    with pytest.raises(ValueError):
        service.update_account_transaction(transaction)

    loaded = repository.get_account_transaction(transaction_id)

    assert loaded is not None
    assert loaded.amount == Decimal("100")


def test_update_missing_account_transaction(
    journal,
) -> None:
    """Verify missing transactions return False."""

    service, repository, _ = journal

    transaction = make_account_transaction(
        AccountTransactionType.DEPOSIT,
        Decimal("100"),
    )

    transaction.transaction_id = 999

    assert service.update_account_transaction(transaction) is False


def test_update_account_transaction_without_id(
    journal,
) -> None:
    """Verify unsaved transactions cannot be updated."""

    service, repository, _ = journal

    transaction = make_account_transaction(
        AccountTransactionType.DEPOSIT,
        Decimal("100"),
    )

    with pytest.raises(ValueError):
        service.update_account_transaction(transaction)


def test_delete_account_transaction(journal) -> None:
    """Verify existing transactions can be deleted."""

    service, repository, _ = journal

    transaction_id = service.create_account_transaction(
        make_account_transaction(
            AccountTransactionType.DEPOSIT,
            Decimal("100"),
        )
    )

    assert service.delete_account_transaction(transaction_id) is True

    assert repository.get_account_transaction(transaction_id) is None


def test_delete_missing_account_transaction(
    journal,
) -> None:
    """Verify missing transaction deletion returns False."""

    service, repository, _ = journal

    assert service.delete_account_transaction(999) is False
