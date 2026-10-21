# =============================================================================
# File: test_account_transfer_financial_integrity.py
# Purpose: Verify financial neutrality and integrity of internal cash transfers.
# =============================================================================

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from stonks.journal.analytics.account_analytics import calculate_account_metrics
from stonks.journal.journal_context import JournalContext
from stonks.journal.models.account_transaction import AccountTransaction
from stonks.journal.models.account_transaction_type import AccountTransactionType
from stonks.journal.models.account_transfer import AccountTransfer
from stonks.journal.models.account_type import AccountType
from stonks.journal.models.trading_account import TradingAccount

OCCURRED_AT = datetime(2026, 10, 21, 16, 0, tzinfo=timezone.utc)


@pytest.fixture
def journal(tmp_path):
    """Provide a clean v3 journal containing two tracked accounts."""
    with JournalContext(tmp_path / "financial_integrity.db") as context:
        source = context.m_service.create_trading_account(TradingAccount("Cash", AccountType.CASH))
        destination = context.m_service.create_trading_account(TradingAccount("Roth IRA", AccountType.ROTH_IRA))
        yield context, source, destination


def metrics(context, account_id):
    """Calculate ledger-only metrics from an account's persisted transactions."""
    return calculate_account_metrics(
        transactions=context.m_repository.get_account_transactions(account_id),
        executions=[],
        positions=[],
    )


def transfer_pair(context, source, destination, amount=Decimal("250.00")):
    """Create an internal transfer and return its persistent pair identifier."""
    out_id, in_id = context.m_service.create_account_transfer(
        source, destination, amount, OCCURRED_AT, "Internal allocation"
    )
    outgoing = context.m_repository.get_account_transaction(out_id)
    incoming = context.m_repository.get_account_transaction(in_id)
    assert outgoing is not None
    assert incoming is not None
    assert outgoing.transfer_id is not None
    assert outgoing.transfer_id == incoming.transfer_id
    return outgoing.transfer_id, out_id, in_id


def deposit(context, account_id, amount):
    """Create a real external deposit through the journal service."""
    return context.m_service.create_account_transaction(
        AccountTransaction(
            transaction_type=AccountTransactionType.DEPOSIT,
            occurred_at=OCCURRED_AT,
            amount=amount,
            account_id=account_id,
            notes="External contribution",
        )
    )


def test_transfer_changes_account_cash_not_contributions_or_pnl(journal):
    """Moving tracked cash is not a deposit, withdrawal, or trading profit."""
    context, source, destination = journal
    deposit(context, source, Decimal("1000.00"))
    transfer_pair(context, source, destination)

    sending = metrics(context, source)
    receiving = metrics(context, destination)

    assert sending.cash_balance == Decimal("750.00")
    assert receiving.cash_balance == Decimal("250.00")
    assert sending.total_deposits == Decimal("1000.00")
    assert receiving.total_deposits == Decimal("0")
    assert sending.total_withdrawals == receiving.total_withdrawals == Decimal("0")
    assert sending.net_contributions == Decimal("1000.00")
    assert receiving.net_contributions == Decimal("0")
    assert sending.realized_trading_pnl == receiving.realized_trading_pnl == Decimal("0")
    assert sending.net_realized_pnl == receiving.net_realized_pnl == Decimal("0")
    assert sending.equity_at_cost_basis == Decimal("750.00")
    assert receiving.equity_at_cost_basis == Decimal("250.00")
    assert sending.cash_balance + receiving.cash_balance == Decimal("1000.00")


def test_transfer_without_recorded_opening_cash_is_allowed_and_neutral(journal):
    """No balance-limit rule applies until opening balances are supported."""
    context, source, destination = journal
    transfer_pair(context, source, destination, Decimal("123.45"))

    sending = metrics(context, source)
    receiving = metrics(context, destination)
    assert sending.cash_balance == Decimal("-123.45")
    assert receiving.cash_balance == Decimal("123.45")
    assert sending.cash_balance + receiving.cash_balance == Decimal("0")
    assert sending.net_contributions + receiving.net_contributions == Decimal("0")


def test_editing_transfer_preserves_portfolio_cash_and_contributions(journal):
    """Changing a transfer amount updates allocation, never total capital."""
    context, source, destination = journal
    deposit(context, source, Decimal("1000.00"))
    transfer_id, out_id, in_id = transfer_pair(context, source, destination)

    updated = AccountTransfer(
        source_account_id=source,
        destination_account_id=destination,
        amount=Decimal("625.75"),
        occurred_at=OCCURRED_AT,
        notes="Reallocated",
        transfer_id=transfer_id,
    )
    assert context.m_service.update_account_transfer(updated)

    sending = metrics(context, source)
    receiving = metrics(context, destination)
    assert sending.cash_balance == Decimal("374.25")
    assert receiving.cash_balance == Decimal("625.75")
    assert sending.cash_balance + receiving.cash_balance == Decimal("1000.00")
    assert sending.net_contributions + receiving.net_contributions == Decimal("1000.00")
    assert sending.net_realized_pnl + receiving.net_realized_pnl == Decimal("0")
    assert context.m_repository.get_account_transaction(out_id).amount == Decimal("625.75")
    assert context.m_repository.get_account_transaction(in_id).amount == Decimal("625.75")


def test_deleting_transfer_restores_cash_allocation(journal):
    """Removing both legs restores original cash without changing contributions."""
    context, source, destination = journal
    deposit(context, source, Decimal("1000.00"))
    transfer_id, _, _ = transfer_pair(context, source, destination)
    assert context.m_service.delete_account_transfer(transfer_id)

    sending = metrics(context, source)
    receiving = metrics(context, destination)
    assert sending.cash_balance == Decimal("1000.00")
    assert receiving.cash_balance == Decimal("0")
    assert sending.net_contributions == Decimal("1000.00")
    assert receiving.net_contributions == Decimal("0")
    assert context.m_connection.execute("SELECT COUNT(*) FROM account_transfers").fetchone()[0] == 0


def test_multiple_transfers_are_net_zero_across_accounts(journal):
    """Opposing and fractional transfers do not manufacture cash."""
    context, source, destination = journal
    deposit(context, source, Decimal("100.00"))
    transfer_pair(context, source, destination, Decimal("67.19"))
    transfer_pair(context, destination, source, Decimal("19.07"))

    sending = metrics(context, source)
    receiving = metrics(context, destination)
    assert sending.cash_balance == Decimal("51.88")
    assert receiving.cash_balance == Decimal("48.12")
    assert sending.cash_balance + receiving.cash_balance == Decimal("100.00")
    assert sending.net_contributions + receiving.net_contributions == Decimal("100.00")


def test_archiving_account_preserves_historical_transfer_metrics(journal):
    """Archiving an account does not erase prior cash movements."""
    context, source, destination = journal
    deposit(context, source, Decimal("100.00"))
    transfer_pair(context, source, destination, Decimal("40.00"))
    assert context.m_service.archive_trading_account(destination)

    assert metrics(context, source).cash_balance == Decimal("60.00")
    assert metrics(context, destination).cash_balance == Decimal("40.00")
    assert metrics(context, destination).net_contributions == Decimal("0")


def test_persisted_transfer_legs_match_parent_and_have_opposite_signs(journal):
    """Every paired ledger record agrees with its parent and opposite leg."""
    context, source, destination = journal
    transfer_id, out_id, in_id = transfer_pair(context, source, destination)
    parent = context.m_connection.execute(
        "SELECT * FROM account_transfers WHERE transfer_id = ?", (transfer_id,)
    ).fetchone()
    outgoing = context.m_repository.get_account_transaction(out_id)
    incoming = context.m_repository.get_account_transaction(in_id)

    assert parent is not None
    assert outgoing.transaction_type == AccountTransactionType.TRANSFER_OUT
    assert incoming.transaction_type == AccountTransactionType.TRANSFER_IN
    assert parent["source_account_id"] == outgoing.account_id == source
    assert parent["destination_account_id"] == incoming.account_id == destination
    assert Decimal(parent["amount"]) == outgoing.amount == incoming.amount
    assert outgoing.occurred_at == incoming.occurred_at
    assert parent["notes"] == outgoing.notes == incoming.notes
    assert outgoing.net_cash_flow == -incoming.net_cash_flow
    assert len(context.m_repository.get_account_transactions()) == 2
