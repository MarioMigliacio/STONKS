"""Atomic inter-account transfer tests for the STONKS journal backend."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from stonks.journal.journal_context import JournalContext
from stonks.journal.models.account_transaction_type import AccountTransactionType
from stonks.journal.models.account_type import AccountType
from stonks.journal.models.opening_cash_balance import OpeningCashBalance
from stonks.journal.models.trading_account import TradingAccount
from stonks.journal.persistence.opening_cash_repository import OpeningCashRepository


@pytest.fixture
def transfer_journal(tmp_path):
    """Provide two funded trading accounts for transfer tests."""
    with JournalContext(tmp_path / "transfer.db") as context:
        source = context.m_service.create_trading_account(TradingAccount("Cash", AccountType.CASH))
        destination = context.m_service.create_trading_account(TradingAccount("IRA", AccountType.ROTH_IRA))

        opening_repo = OpeningCashRepository(context.m_connection)
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)

        with context.m_connection:
            opening_repo.upsert(OpeningCashBalance(source, Decimal("10000"), start))
            opening_repo.upsert(OpeningCashBalance(destination, Decimal("10000"), start))

        yield context, source, destination


def test_transfer_creates_two_balanced_records(transfer_journal):
    """Both transfer legs share amount, timestamp and opposite cash effects."""
    context, source, destination = transfer_journal
    date = datetime(2026, 10, 20, 12, 30, tzinfo=timezone(timedelta(hours=-7)))

    out_id, in_id = context.m_service.create_account_transfer(
        source, destination, Decimal("125.25"), date, "Internal reallocation"
    )

    outgoing = context.m_repository.get_account_transaction(out_id)
    incoming = context.m_repository.get_account_transaction(in_id)
    assert outgoing.account_id == source
    assert incoming.account_id == destination
    assert outgoing.transaction_type is AccountTransactionType.TRANSFER_OUT
    assert incoming.transaction_type is AccountTransactionType.TRANSFER_IN
    assert outgoing.amount == incoming.amount == Decimal("125.25")
    assert outgoing.occurred_at == incoming.occurred_at == date.astimezone(timezone.utc)
    assert outgoing.net_cash_flow + incoming.net_cash_flow == 0
    assert outgoing.notes == incoming.notes == "Internal reallocation"


def test_transfer_rollback_when_second_insert_fails(transfer_journal, monkeypatch):
    """An error creating the incoming leg must roll back the outgoing leg."""
    context, source, destination = transfer_journal
    original_insert = context.m_service.m_repository.create_account_transaction
    calls = 0

    def failing_insert(transaction):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("Simulated destination insert failure")
        return original_insert(transaction)

    monkeypatch.setattr(context.m_service.m_repository, "create_account_transaction", failing_insert)
    with pytest.raises(RuntimeError, match="Simulated"):
        context.m_service.create_account_transfer(source, destination, Decimal("100"), datetime.now(timezone.utc))
    assert context.m_repository.get_account_transactions(source) == []
    assert context.m_repository.get_account_transactions(destination) == []
    assert not context.m_connection.in_transaction


@pytest.mark.parametrize("amount", [Decimal("0"), Decimal("-5"), Decimal("NaN"), Decimal("Infinity"), 3.5])
def test_transfer_rejects_invalid_amount(transfer_journal, amount):
    """Transfer amounts must be finite positive Decimal values."""
    context, source, destination = transfer_journal
    with pytest.raises(ValueError):
        context.m_service.create_account_transfer(source, destination, amount, datetime.now(timezone.utc))
    assert context.m_repository.get_account_transactions() == []


def test_transfer_rejects_same_account_and_naive_datetime(transfer_journal):
    """A transfer needs two different accounts and an aware timestamp."""
    context, source, destination = transfer_journal
    with pytest.raises(ValueError):
        context.m_service.create_account_transfer(source, source, Decimal("10"), datetime.now(timezone.utc))
    with pytest.raises(ValueError):
        context.m_service.create_account_transfer(source, destination, Decimal("10"), datetime(2026, 10, 20))
    assert context.m_repository.get_account_transactions() == []


def test_transfer_rejects_archived_destination(transfer_journal):
    """Transfer fails cleanly if either trading account is archived."""
    context, source, destination = transfer_journal
    assert context.m_service.archive_trading_account(destination)
    with pytest.raises(ValueError, match="archived"):
        context.m_service.create_account_transfer(source, destination, Decimal("10"), datetime.now(timezone.utc))
    assert context.m_repository.get_account_transactions() == []


def test_transfer_rejects_nonexistent_account(transfer_journal):
    """No transfer leg is saved when its destination does not exist."""
    context, source, _ = transfer_journal
    with pytest.raises(ValueError, match="does not exist"):
        context.m_service.create_account_transfer(source, 999999, Decimal("10"), datetime.now(timezone.utc))
    assert context.m_repository.get_account_transactions() == []
