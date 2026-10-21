# =============================================================================
# File: test_cash_mutation_guards.py
# Purpose: Prevent ordinary ledger mutations from invalidating cash transfers.
# =============================================================================

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from stonks.journal.journal_context import JournalContext
from stonks.journal.models.account_transaction import AccountTransaction
from stonks.journal.models.account_transaction_type import AccountTransactionType
from stonks.journal.models.account_type import AccountType
from stonks.journal.models.opening_cash_balance import OpeningCashBalance
from stonks.journal.models.trading_account import TradingAccount
from stonks.journal.persistence.opening_cash_repository import OpeningCashRepository

START = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)


@pytest.fixture
def journal(tmp_path):
    """Create funded cash accounts with isolated ledger histories."""
    with JournalContext(tmp_path / "d36a.db") as context:
        account_ids = [
            context.m_service.create_trading_account(TradingAccount(name, AccountType.CASH))
            for name in ("Source", "Intermediate", "Destination")
        ]
        opening_repo = OpeningCashRepository(context.m_connection)
        with context.m_connection:
            for account_id, amount in zip(account_ids, ("100", "0", "0")):
                opening_repo.upsert(OpeningCashBalance(account_id, Decimal(amount), START))
        yield context, account_ids


def add_transaction(context, account_id, kind, amount, day):
    """Record a real transaction through the service."""
    return context.m_service.create_account_transaction(
        AccountTransaction(
            transaction_type=kind,
            occurred_at=START + timedelta(days=day),
            amount=Decimal(amount),
            account_id=account_id,
        )
    )


def transfer(context, source, destination, amount, day):
    """Record a linked two-leg transfer."""
    outgoing_id, incoming_id = context.m_service.create_account_transfer(
        source,
        destination,
        Decimal(amount),
        START + timedelta(days=day),
    )
    linked = context.m_repository.get_account_transaction(outgoing_id)
    return linked.transfer_id, outgoing_id, incoming_id


def test_deleting_incoming_transfer_cannot_break_later_transfer(journal):
    """Removing an upstream incoming leg must not strand downstream cash."""
    context, (source, middle, destination) = journal
    earlier_id, out_id, in_id = transfer(context, source, middle, "80", 1)
    transfer(context, middle, destination, "70", 2)

    with pytest.raises(ValueError, match="Insufficient"):
        context.m_service.delete_account_transfer(earlier_id)

    assert context.m_repository.get_account_transaction(out_id) is not None
    assert context.m_repository.get_account_transaction(in_id) is not None
    assert context.m_connection.execute("SELECT COUNT(*) FROM account_transfers").fetchone()[0] == 2
    assert not context.m_connection.in_transaction


def test_deleting_safe_transfer_succeeds(journal):
    """Deleting an isolated transfer keeps atomic paired cleanup."""
    context, (source, middle, _) = journal
    transfer_id, outgoing_id, incoming_id = transfer(context, source, middle, "40", 1)

    assert context.m_service.delete_account_transfer(transfer_id)
    assert context.m_repository.get_account_transaction(outgoing_id) is None
    assert context.m_repository.get_account_transaction(incoming_id) is None
    assert not context.m_connection.in_transaction


def test_reducing_prior_deposit_cannot_undermine_transfer(journal):
    """A previously funded transfer must survive edits of its funding deposit."""
    context, (source, middle, _) = journal
    deposit_id = add_transaction(context, source, AccountTransactionType.DEPOSIT, "100", 1)
    transfer(context, source, middle, "150", 2)
    original = context.m_repository.get_account_transaction(deposit_id)

    with pytest.raises(ValueError, match="Insufficient"):
        context.m_service.update_account_transaction(replace(original, amount=Decimal("20")))

    assert context.m_repository.get_account_transaction(deposit_id).amount == Decimal("100")
    assert not context.m_connection.in_transaction


def test_deleting_funding_deposit_rolls_back(journal):
    """Deleting a necessary contribution cannot corrupt later transfer history."""
    context, (source, middle, _) = journal
    deposit_id = add_transaction(context, source, AccountTransactionType.DEPOSIT, "100", 1)
    transfer(context, source, middle, "150", 2)

    with pytest.raises(ValueError, match="Insufficient"):
        context.m_service.delete_account_transaction(deposit_id)

    assert context.m_repository.get_account_transaction(deposit_id) is not None
    assert not context.m_connection.in_transaction


def test_backdating_funding_deposit_after_transfer_is_rejected(journal):
    """Moving a deposit later must not retroactively unfund a transfer."""
    context, (source, middle, _) = journal
    deposit_id = add_transaction(context, source, AccountTransactionType.DEPOSIT, "100", 1)
    transfer(context, source, middle, "150", 2)
    original = context.m_repository.get_account_transaction(deposit_id)

    with pytest.raises(ValueError, match="Insufficient"):
        context.m_service.update_account_transaction(replace(original, occurred_at=START + timedelta(days=3)))

    assert context.m_repository.get_account_transaction(deposit_id).occurred_at == original.occurred_at


def test_new_negative_adjustment_cannot_undermine_transfer(journal):
    """An added cash outflow must not invalidate an existing later transfer."""
    context, (source, middle, _) = journal
    transfer(context, source, middle, "90", 2)

    with pytest.raises(ValueError, match="Insufficient"):
        add_transaction(context, source, AccountTransactionType.ADJUSTMENT, "-20", 1)

    assert len(context.m_repository.get_account_transactions(source)) == 1
    assert not context.m_connection.in_transaction


def test_ordinary_transaction_without_transfers_is_unchanged(journal):
    """D3.6A does not yet enforce overdrafts on accounts without transfers."""
    context, (source, _, _) = journal
    tx_id = add_transaction(context, source, AccountTransactionType.WITHDRAWAL, "120", 1)
    assert context.m_repository.get_account_transaction(tx_id) is not None


def test_pre_snapshot_deposit_edit_does_not_rewrite_starting_cash(journal):
    """Older history may be corrected without double-counting dated opening cash."""
    context, (source, middle, _) = journal
    deposit_id = add_transaction(context, source, AccountTransactionType.DEPOSIT, "40", -1)
    transfer(context, source, middle, "60", 1)
    old = context.m_repository.get_account_transaction(deposit_id)

    assert context.m_service.update_account_transaction(replace(old, amount=Decimal("10")))
    assert context.m_repository.get_account_transaction(deposit_id).amount == Decimal("10")
