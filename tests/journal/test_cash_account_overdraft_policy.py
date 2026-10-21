# =============================================================================
# File: test_cash_account_overdraft_policy.py
# Purpose: Verify strict cash policy for funded non-margin journal accounts.
# =============================================================================

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from stonks.journal.journal_context import JournalContext
from stonks.journal.models.account_transaction import AccountTransaction
from stonks.journal.models.account_transaction_type import AccountTransactionType
from stonks.journal.models.account_type import AccountType
from stonks.journal.models.execution_side import ExecutionSide
from stonks.journal.models.opening_cash_balance import OpeningCashBalance
from stonks.journal.models.position import Position
from stonks.journal.models.trade_execution import TradeExecution
from stonks.journal.models.trading_account import TradingAccount

START = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)


@pytest.fixture
def journal(tmp_path):
    """Provide isolated service and repository access to a temporary database."""
    with JournalContext(tmp_path / "cash_policy.db") as context:
        yield context


def make_account(context, kind, opening="100"):
    """Create an account and optionally establish a verified cash baseline."""
    account_id = context.m_service.create_trading_account(
        TradingAccount(f"Policy {kind.value} {len(context.m_repository.get_trading_accounts())}", kind)
    )

    if opening is not None:
        context.m_service.set_opening_cash(OpeningCashBalance(account_id, Decimal(opening), START))

    return account_id


def record(context, account_id, kind, amount, day=1):
    """Create an independent cash-ledger entry through the journal service."""
    return context.m_service.create_account_transaction(
        AccountTransaction(
            transaction_type=kind,
            occurred_at=START + timedelta(days=day),
            amount=Decimal(amount),
            account_id=account_id,
        )
    )


def fill(position_id, side, shares, price, day=1, fees="0"):
    """Represent a dated trade execution with Decimal monetary values."""
    return TradeExecution(
        position_id=position_id,
        side=side,
        executed_at=START + timedelta(days=day),
        shares=Decimal(shares),
        price=Decimal(price),
        fees=Decimal(fees),
    )


@pytest.mark.parametrize("kind", [AccountType.CASH, AccountType.ROTH_IRA, AccountType.TRADITIONAL_IRA])
def test_funded_non_margin_accounts_reject_overdrawn_withdrawals(journal, kind):
    """A verified opening balance is authoritative for cash-style accounts."""
    account_id = make_account(journal, kind)

    with pytest.raises(ValueError, match="Insufficient"):
        record(journal, account_id, AccountTransactionType.WITHDRAWAL, "101")

    assert journal.m_repository.get_account_transactions(account_id) == []
    assert not journal.m_connection.in_transaction


@pytest.mark.parametrize("kind", [AccountTransactionType.FEE, AccountTransactionType.ADJUSTMENT])
def test_fee_or_negative_adjustment_cannot_overdraw(journal, kind):
    """Standalone fees and corrections must respect verified cash."""
    account_id = make_account(journal, AccountType.CASH)
    amount = "110" if kind == AccountTransactionType.FEE else "-110"

    with pytest.raises(ValueError, match="Insufficient"):
        record(journal, account_id, kind, amount)

    assert journal.m_repository.get_account_transactions(account_id) == []


def test_backdated_withdrawal_cannot_overdraw_before_later_deposit(journal):
    """An eventual positive balance does not erase an earlier deficit."""
    account_id = make_account(journal, AccountType.CASH)
    record(journal, account_id, AccountTransactionType.DEPOSIT, "100", day=3)

    with pytest.raises(ValueError, match="Insufficient"):
        record(journal, account_id, AccountTransactionType.WITHDRAWAL, "150", day=2)

    assert len(journal.m_repository.get_account_transactions(account_id)) == 1


def test_deleting_funding_deposit_without_transfers_rolls_back(journal):
    """Deposit deletion cannot strand an independent later withdrawal."""
    account_id = make_account(journal, AccountType.CASH)
    deposit_id = record(journal, account_id, AccountTransactionType.DEPOSIT, "100", day=1)
    record(journal, account_id, AccountTransactionType.WITHDRAWAL, "150", day=2)

    with pytest.raises(ValueError, match="Insufficient"):
        journal.m_service.delete_account_transaction(deposit_id)

    assert journal.m_repository.get_account_transaction(deposit_id) is not None
    assert not journal.m_connection.in_transaction


def test_editing_withdrawal_to_overdraft_is_rejected(journal):
    """A rejected amendment retains the original transaction values."""
    account_id = make_account(journal, AccountType.CASH)
    entry_id = record(journal, account_id, AccountTransactionType.WITHDRAWAL, "40")
    original = journal.m_repository.get_account_transaction(entry_id)

    with pytest.raises(ValueError, match="Insufficient"):
        journal.m_service.update_account_transaction(replace(original, amount=Decimal("120")))

    assert journal.m_repository.get_account_transaction(entry_id).amount == Decimal("40")


def test_trade_purchase_and_fees_cannot_overdraw(journal):
    """Cash-account buys include execution fees in cash checks."""
    account_id = make_account(journal, AccountType.CASH)
    position_id = journal.m_service.create_position(Position("NVDA", account_id=account_id))

    with pytest.raises(ValueError, match="Insufficient"):
        journal.m_service.create_execution(fill(position_id, ExecutionSide.BUY, "2", "50", fees="0.01"))

    assert journal.m_repository.get_position_executions(position_id) == []
    assert not journal.m_connection.in_transaction


def test_editing_trade_buy_cannot_overdraw(journal):
    """Updating a valid buy rolls back if its new cost exceeds cash."""
    account_id = make_account(journal, AccountType.CASH)
    position_id = journal.m_service.create_position(Position("AMD", account_id=account_id))
    execution_id = journal.m_service.create_execution(fill(position_id, ExecutionSide.BUY, "1", "60"))
    existing = journal.m_repository.get_execution(execution_id)

    with pytest.raises(ValueError, match="Insufficient"):
        journal.m_service.update_execution(replace(existing, price=Decimal("120")))

    assert journal.m_repository.get_execution(execution_id).price == Decimal("60")


def test_margin_account_without_transfers_can_record_negative_cash(journal):
    """A margin account's debit balance is not treated as an error here."""
    account_id = make_account(journal, AccountType.MARGIN)
    entry_id = record(journal, account_id, AccountTransactionType.WITHDRAWAL, "130")

    assert journal.m_repository.get_account_transaction(entry_id) is not None


def test_missing_opening_baseline_keeps_journal_entry_unverified(journal):
    """A missing snapshot is not silently converted into an assumed zero."""
    account_id = make_account(journal, AccountType.CASH, opening=None)
    entry_id = record(journal, account_id, AccountTransactionType.WITHDRAWAL, "100")

    assert journal.m_repository.get_account_transaction(entry_id) is not None


def test_pre_snapshot_transaction_does_not_affect_verified_cash(journal):
    """Editing superseded history does not change post-snapshot cash."""
    account_id = make_account(journal, AccountType.CASH)
    entry_id = record(journal, account_id, AccountTransactionType.WITHDRAWAL, "500", day=-1)

    assert journal.m_repository.get_account_transaction(entry_id) is not None


def test_lowering_opening_cash_without_transfers_is_rejected(journal):
    """Editing the baseline cannot invalidate subsequent independent spending."""
    account_id = make_account(journal, AccountType.CASH)
    record(journal, account_id, AccountTransactionType.WITHDRAWAL, "70")

    with pytest.raises(ValueError, match="Insufficient"):
        journal.m_service.set_opening_cash(OpeningCashBalance(account_id, Decimal("50"), START))

    row = journal.m_connection.execute(
        "SELECT amount FROM account_opening_cash WHERE account_id = ?", (account_id,)
    ).fetchone()
    assert Decimal(row["amount"]) == Decimal("100")
