"""Integration regression tests for opening-cash-backed transfer enforcement."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from stonks.journal.journal_context import JournalContext
from stonks.journal.models.account_transaction import AccountTransaction
from stonks.journal.models.account_transaction_type import AccountTransactionType
from stonks.journal.models.account_transfer import AccountTransfer
from stonks.journal.models.account_type import AccountType
from stonks.journal.models.opening_cash_balance import OpeningCashBalance
from stonks.journal.models.trading_account import TradingAccount
from stonks.journal.persistence.opening_cash_repository import OpeningCashRepository

START = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)


@pytest.fixture
def accounts(tmp_path):
    """Provide tracked accounts with a known, funded starting cash ledger."""
    with JournalContext(tmp_path / "transfer_enforcement.db") as context:
        source = context.m_service.create_trading_account(TradingAccount("Cash", AccountType.CASH))
        destination = context.m_service.create_trading_account(TradingAccount("IRA", AccountType.ROTH_IRA))
        openings = OpeningCashRepository(context.m_connection)
        with context.m_connection:
            openings.upsert(OpeningCashBalance(source, Decimal("1000"), START))
            openings.upsert(OpeningCashBalance(destination, Decimal("0"), START))
        yield context, source, destination


def test_create_enforces_available_cash(accounts):
    """Reject unaffordable transfer before writing a parent or either leg."""
    context, source, destination = accounts
    with pytest.raises(ValueError, match="Insufficient"):
        context.m_service.create_account_transfer(source, destination, Decimal("1000.01"), START)
    assert context.m_repository.get_account_transactions() == []
    assert context.m_connection.execute("SELECT count(*) FROM account_transfers").fetchone()[0] == 0
    assert not context.m_connection.in_transaction


def test_create_requires_both_opening_snapshots(accounts):
    """A missing destination baseline is unknown, not zero."""
    context, source, _ = accounts
    third = context.m_service.create_trading_account(TradingAccount("Other", AccountType.CASH))
    with pytest.raises(ValueError, match="opening cash"):
        context.m_service.create_account_transfer(source, third, Decimal("5"), START)
    assert context.m_connection.execute("SELECT count(*) FROM account_transfers").fetchone()[0] == 0


def test_create_checks_later_withdrawals(accounts):
    """Past transfer cannot cause a future recorded cash deficit."""
    context, source, destination = accounts
    context.m_service.create_account_transaction(
        AccountTransaction(
            AccountTransactionType.WITHDRAWAL, START + timedelta(days=5), Decimal("800"), account_id=source
        )
    )
    with pytest.raises(ValueError, match="Insufficient"):
        context.m_service.create_account_transfer(source, destination, Decimal("250"), START + timedelta(days=1))


def test_edit_restores_old_pair_before_reprojection(accounts):
    """A transfer edit must not double-count the existing outgoing leg."""
    context, source, destination = accounts
    out_id, in_id = context.m_service.create_account_transfer(source, destination, Decimal("300"), START)
    old = context.m_repository.get_account_transaction(out_id)
    proposed = AccountTransfer(
        source, destination, Decimal("900"), START + timedelta(days=1), transfer_id=old.transfer_id
    )
    assert context.m_service.update_account_transfer(proposed)
    assert context.m_repository.get_account_transaction(out_id).amount == Decimal("900")
    assert context.m_repository.get_account_transaction(in_id).amount == Decimal("900")


def test_edit_rejection_preserves_pair(accounts):
    """Rejected edits leave parent and both legs intact and release the transaction."""
    context, source, destination = accounts
    out_id, in_id = context.m_service.create_account_transfer(source, destination, Decimal("300"), START)
    old = context.m_repository.get_account_transaction(out_id)
    proposed = AccountTransfer(source, destination, Decimal("1200"), START, transfer_id=old.transfer_id)
    with pytest.raises(ValueError, match="Insufficient"):
        context.m_service.update_account_transfer(proposed)
    assert context.m_repository.get_account_transaction(out_id).amount == Decimal("300")
    assert context.m_repository.get_account_transaction(in_id).amount == Decimal("300")
    assert (
        context.m_connection.execute(
            "SELECT amount FROM account_transfers WHERE transfer_id = ?", (old.transfer_id,)
        ).fetchone()[0]
        == "300"
    )
    assert not context.m_connection.in_transaction


def test_transfer_before_opening_is_rejected(accounts):
    """Cannot spend before the recorded starting-cash instant."""
    context, source, destination = accounts
    with pytest.raises(ValueError, match="precede"):
        context.m_service.create_account_transfer(source, destination, Decimal("5"), START - timedelta(seconds=1))
