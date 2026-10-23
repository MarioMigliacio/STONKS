# =============================================================================
# File: test_account_transfer_edit_delete.py
# Purpose: Pytest file for test_account_transfer_edit_delete.py.
# =============================================================================

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from stonks.journal.journal_context import JournalContext
from stonks.journal.models.account_transfer import AccountTransfer
from stonks.journal.models.account_type import AccountType
from stonks.journal.models.opening_cash_balance import OpeningCashBalance
from stonks.journal.models.trading_account import TradingAccount
from stonks.journal.persistence.opening_cash_repository import OpeningCashRepository


@pytest.fixture
def journal(tmp_path):
    """Create linked transfer records in a temporary v3 database."""
    with JournalContext(tmp_path / "d32.db") as context:
        source = context.m_service.create_trading_account(TradingAccount("Cash", AccountType.CASH))
        destination = context.m_service.create_trading_account(TradingAccount("Roth", AccountType.ROTH_IRA))

        opening_repo = OpeningCashRepository(context.m_connection)
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)

        with context.m_connection:
            opening_repo.upsert(OpeningCashBalance(source, Decimal("10000"), start))
            opening_repo.upsert(OpeningCashBalance(destination, Decimal("10000"), start))

        out_id, in_id = context.m_service.create_account_transfer(
            source, destination, Decimal("100"), datetime(2026, 10, 21, tzinfo=timezone.utc), "Original"
        )
        outgoing = context.m_repository.get_account_transaction(out_id)
        assert outgoing is not None
        assert outgoing.transfer_id is not None
        yield context, source, destination, outgoing.transfer_id, out_id, in_id


def proposed(transfer_id, source, destination, amount="125", notes="Updated"):
    """Build a requested transfer amendment."""
    return AccountTransfer(
        source_account_id=source,
        destination_account_id=destination,
        amount=Decimal(amount),
        occurred_at=datetime(2026, 10, 22, tzinfo=timezone.utc),
        notes=notes,
        transfer_id=transfer_id,
    )


def get_parent(context, transfer_id):
    """Read the transfer parent row for regression assertions."""
    return context.m_connection.execute(
        "SELECT * FROM account_transfers WHERE transfer_id = ?", (transfer_id,)
    ).fetchone()


def test_update_changes_parent_and_both_legs(journal):
    """Editing a transfer updates linked rows without changing their IDs."""
    context, source, destination, transfer_id, out_id, in_id = journal
    transfer = proposed(transfer_id, source, destination)
    assert context.m_service.update_account_transfer(transfer)
    outgoing = context.m_repository.get_account_transaction(out_id)
    incoming = context.m_repository.get_account_transaction(in_id)
    parent = get_parent(context, transfer_id)
    assert parent["amount"] == "125"
    assert parent["notes"] == "Updated"
    assert outgoing.amount == incoming.amount == Decimal("125")
    assert outgoing.notes == incoming.notes == "Updated"
    assert outgoing.occurred_at == incoming.occurred_at == transfer.occurred_at
    assert outgoing.net_cash_flow + incoming.net_cash_flow == 0
    assert outgoing.transfer_id == incoming.transfer_id == transfer_id


def test_delete_removes_parent_and_both_legs(journal):
    """Deleting a transfer removes both legs and parent atomically."""
    context, _, _, transfer_id, out_id, in_id = journal
    assert context.m_service.delete_account_transfer(transfer_id)
    assert get_parent(context, transfer_id) is None
    assert context.m_repository.get_account_transaction(out_id) is None
    assert context.m_repository.get_account_transaction(in_id) is None
    assert context.m_service.delete_account_transfer(transfer_id) is False


def test_update_rollback_on_second_leg_failure(journal, monkeypatch):
    """Failed incoming-leg update rolls back parent and outgoing changes."""
    context, source, destination, transfer_id, out_id, in_id = journal
    original_update = context.m_service.m_repository.update_account_transaction
    calls = 0

    def fail_on_second_leg(transaction):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("Simulated incoming update failure")
        return original_update(transaction)

    monkeypatch.setattr(context.m_service.m_repository, "update_account_transaction", fail_on_second_leg)
    with pytest.raises(RuntimeError, match="Simulated incoming"):
        context.m_service.update_account_transfer(proposed(transfer_id, source, destination))
    assert get_parent(context, transfer_id)["amount"] == "100"
    assert context.m_repository.get_account_transaction(out_id).amount == Decimal("100")
    assert context.m_repository.get_account_transaction(in_id).amount == Decimal("100")
    assert not context.m_connection.in_transaction


def test_delete_rollback_on_second_leg_failure(journal, monkeypatch):
    """Failed incoming-leg deletion restores outgoing and parent records."""
    context, _, _, transfer_id, out_id, in_id = journal
    original_delete = context.m_service.m_repository.delete_account_transaction
    calls = 0

    def fail_on_second_leg(transaction_id):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("Simulated incoming delete failure")
        return original_delete(transaction_id)

    monkeypatch.setattr(context.m_service.m_repository, "delete_account_transaction", fail_on_second_leg)
    with pytest.raises(RuntimeError, match="Simulated incoming"):
        context.m_service.delete_account_transfer(transfer_id)
    assert get_parent(context, transfer_id) is not None
    assert context.m_repository.get_account_transaction(out_id) is not None
    assert context.m_repository.get_account_transaction(in_id) is not None
    assert not context.m_connection.in_transaction


def test_cannot_change_account_ownership(journal):
    """Ownership changes require a different transfer, not a partial rewrite."""
    context, source, destination, transfer_id, _, _ = journal
    with pytest.raises(ValueError, match="ownership"):
        context.m_service.update_account_transfer(proposed(transfer_id, destination, source))


def test_missing_transfer_returns_false(journal):
    """Missing transfer updates and deletions have predictable results."""
    context, source, destination, _, _, _ = journal
    assert not context.m_service.update_account_transfer(proposed(999999, source, destination))
    assert not context.m_service.delete_account_transfer(999999)


def test_archived_account_blocks_change(journal):
    """Archived accounts make transfers read-only until reactivated."""
    context, source, destination, transfer_id, _, _ = journal
    assert context.m_service.archive_trading_account(destination)
    with pytest.raises(ValueError, match="archived"):
        context.m_service.update_account_transfer(proposed(transfer_id, source, destination))
    with pytest.raises(ValueError, match="archived"):
        context.m_service.delete_account_transfer(transfer_id)
    assert get_parent(context, transfer_id)["amount"] == "100"


@pytest.mark.parametrize("amount", ["0", "-1", "NaN", "Infinity"])
def test_invalid_update_amount_rejected(journal, amount):
    """Invalid amounts never modify persisted transfer records."""
    context, source, destination, transfer_id, _, _ = journal
    with pytest.raises(ValueError):
        context.m_service.update_account_transfer(proposed(transfer_id, source, destination, amount))
    assert get_parent(context, transfer_id)["amount"] == "100"


def test_individual_transfer_legs_still_protected(journal):
    """Existing transaction CRUD may not independently modify linked transfers."""
    context, _, _, _, out_id, _ = journal
    existing = context.m_repository.get_account_transaction(out_id)
    with pytest.raises(ValueError, match="independently"):
        context.m_service.update_account_transaction(replace(existing, notes="Unsafe"))
    with pytest.raises(ValueError, match="independently"):
        context.m_service.delete_account_transaction(out_id)
