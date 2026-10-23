# =============================================================================
# File: test_financial_integrity_matrix.py
# Purpose: Pytest file for test_financial_integrity_matrix.py.
# =============================================================================

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from stonks.journal.journal_context import JournalContext
from stonks.journal.models.account_transaction import AccountTransaction
from stonks.journal.models.account_transaction_type import AccountTransactionType
from stonks.journal.models.account_transfer import AccountTransfer
from stonks.journal.models.account_type import AccountType
from stonks.journal.models.execution_side import ExecutionSide
from stonks.journal.models.opening_cash_balance import OpeningCashBalance
from stonks.journal.models.position import Position
from stonks.journal.models.trade_execution import TradeExecution
from stonks.journal.models.trading_account import TradingAccount

START = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)


@pytest.fixture
def journal(tmp_path):
    """Provide an isolated SQLite-backed journal for each integrity scenario."""
    with JournalContext(tmp_path / "d36c_integrity.db") as context:
        yield context


def account(context, name, kind=AccountType.CASH, opening="0"):
    """Create an account with an optional verified opening cash snapshot."""
    account_id = context.m_service.create_trading_account(TradingAccount(name, kind))

    if opening is not None:
        context.m_service.set_opening_cash(OpeningCashBalance(account_id, Decimal(opening), START))

    return account_id


def ledger(context, account_id, kind, amount, when):
    """Post a dated account transaction through the public journal service."""
    return context.m_service.create_account_transaction(
        AccountTransaction(
            transaction_type=kind,
            occurred_at=when,
            amount=Decimal(amount),
            account_id=account_id,
        )
    )


def move(context, source, destination, amount, when):
    """Record a linked internal transfer and return its parent and leg IDs."""
    outgoing_id, incoming_id = context.m_service.create_account_transfer(
        source,
        destination,
        Decimal(amount),
        when,
    )
    outgoing = context.m_repository.get_account_transaction(outgoing_id)

    return outgoing.transfer_id, outgoing_id, incoming_id


def buy_or_sell(context, position_id, side, shares, price, when, fees="0"):
    """Record one validated trade fill with precise signed cash effects."""
    return context.m_service.create_execution(
        TradeExecution(
            position_id=position_id,
            side=side,
            executed_at=when,
            shares=Decimal(shares),
            price=Decimal(price),
            fees=Decimal(fees),
        )
    )


def assert_transaction_closed(context):
    """Check rejection leaves no SQLite service transaction open."""
    assert not context.m_connection.in_transaction


def test_transfer_chain_rejects_deleting_its_upstream_funding(journal):
    """Removing an upstream transfer cannot strand a later outgoing leg."""
    source = account(journal, "Source", opening="200")
    middle = account(journal, "Middle")
    target = account(journal, "Target")

    upstream_id, outgoing_id, incoming_id = move(journal, source, middle, "150", START + timedelta(days=1))
    move(journal, middle, target, "125", START + timedelta(days=2))

    with pytest.raises(ValueError, match="Insufficient"):
        journal.m_service.delete_account_transfer(upstream_id)

    assert journal.m_repository.get_account_transaction(outgoing_id) is not None
    assert journal.m_repository.get_account_transaction(incoming_id) is not None
    assert journal.m_connection.execute("SELECT COUNT(*) FROM account_transfers").fetchone()[0] == 2
    assert_transaction_closed(journal)


def test_backdated_deposit_edit_cannot_unfund_a_transfer(journal):
    """Moving a funding deposit after its dependent transfer must roll back."""
    source = account(journal, "Source", opening="30")
    target = account(journal, "Target")
    deposit_id = ledger(
        journal,
        source,
        AccountTransactionType.DEPOSIT,
        "80",
        START + timedelta(days=1),
    )
    move(journal, source, target, "90", START + timedelta(days=2))
    original = journal.m_repository.get_account_transaction(deposit_id)

    with pytest.raises(ValueError, match="Insufficient"):
        journal.m_service.update_account_transaction(replace(original, occurred_at=START + timedelta(days=3)))

    assert journal.m_repository.get_account_transaction(deposit_id) == original
    assert_transaction_closed(journal)


def test_deleting_sale_proceeds_cannot_strand_another_position(journal):
    """A sale deletion must preserve both position validity and later cash."""
    owner = account(journal, "Cash", opening="100")
    first = journal.m_service.create_position(Position("AMD", account_id=owner))
    second = journal.m_service.create_position(Position("NVDA", account_id=owner))

    buy_or_sell(journal, first, ExecutionSide.BUY, "1", "100", START + timedelta(days=1))
    sell_id = buy_or_sell(journal, first, ExecutionSide.SELL, "1", "100", START + timedelta(days=2))
    buy_or_sell(journal, second, ExecutionSide.BUY, "1", "90", START + timedelta(days=3))

    with pytest.raises(ValueError, match="Insufficient"):
        journal.m_service.delete_execution(sell_id)

    assert journal.m_repository.get_execution(sell_id) is not None
    assert len(journal.m_repository.get_position_executions(first)) == 2
    assert_transaction_closed(journal)


def test_backdated_buy_cannot_spend_before_a_deposit(journal):
    """A later deposit must not finance a chronologically earlier purchase."""
    owner = account(journal, "Cash", opening="20")
    position_id = journal.m_service.create_position(Position("TSLA", account_id=owner))
    ledger(
        journal,
        owner,
        AccountTransactionType.DEPOSIT,
        "100",
        START + timedelta(days=2),
    )

    with pytest.raises(ValueError, match="Insufficient"):
        buy_or_sell(
            journal,
            position_id,
            ExecutionSide.BUY,
            "1",
            "90",
            START + timedelta(days=1),
        )

    assert journal.m_repository.get_position_executions(position_id) == []
    assert_transaction_closed(journal)


def test_same_instant_credit_and_debit_are_combined(journal):
    """Cash at a shared timestamp is validated without arbitrary row ordering."""
    owner = account(journal, "Cash", opening="0")
    when = START + timedelta(hours=1)

    ledger(journal, owner, AccountTransactionType.DEPOSIT, "75", when)
    ledger(journal, owner, AccountTransactionType.WITHDRAWAL, "75", when)

    assert len(journal.m_repository.get_account_transactions(owner)) == 2
    assert_transaction_closed(journal)


def test_timezone_offsets_represent_the_same_cash_instant(journal):
    """Timezone-equivalent timestamps must not produce false overdrafts."""
    owner = account(journal, "Cash", opening="0")
    same_instant = START + timedelta(days=1)
    pacific = same_instant.astimezone(timezone(timedelta(hours=-7)))

    ledger(journal, owner, AccountTransactionType.DEPOSIT, "45", pacific)
    ledger(journal, owner, AccountTransactionType.WITHDRAWAL, "45", same_instant)

    assert len(journal.m_repository.get_account_transactions(owner)) == 2
    assert_transaction_closed(journal)


def test_opening_date_cannot_move_past_linked_transfer(journal):
    """A rejected snapshot date revision must preserve the saved baseline."""
    source = account(journal, "Source", opening="100")
    target = account(journal, "Target")
    move(journal, source, target, "60", START + timedelta(days=1))

    with pytest.raises(ValueError, match="after an existing transfer"):
        journal.m_service.set_opening_cash(OpeningCashBalance(source, Decimal("100"), START + timedelta(days=2)))

    row = journal.m_connection.execute(
        "SELECT amount, effective_at FROM account_opening_cash WHERE account_id = ?",
        (source,),
    ).fetchone()
    assert Decimal(row["amount"]) == Decimal("100")
    assert datetime.fromisoformat(row["effective_at"]) == START
    assert_transaction_closed(journal)


def test_margin_debit_is_allowed_without_transfers(journal):
    """Non-transfer margin activity is not subject to the cash-account rule."""
    owner = account(journal, "Margin", kind=AccountType.MARGIN, opening="10")
    position_id = journal.m_service.create_position(Position("AMD", account_id=owner))

    execution_id = buy_or_sell(journal, position_id, ExecutionSide.BUY, "2", "75", START + timedelta(days=1))

    assert journal.m_repository.get_execution(execution_id) is not None
    assert_transaction_closed(journal)


def test_missing_opening_preserves_unverified_ordinary_history(journal):
    """The journal accepts unverified entries but cannot fund a linked transfer."""
    source = account(journal, "Unverified", opening=None)
    target = account(journal, "Target", opening="0")
    ledger(
        journal,
        source,
        AccountTransactionType.WITHDRAWAL,
        "80",
        START + timedelta(days=1),
    )

    with pytest.raises(ValueError, match="opening cash"):
        move(journal, source, target, "10", START + timedelta(days=2))

    assert len(journal.m_repository.get_account_transactions(source)) == 1
    assert_transaction_closed(journal)


def test_archived_account_blocks_changes_without_erasing_history(journal):
    """Archived-account protection remains active across cash mutations."""
    source = account(journal, "Source", opening="100")
    target = account(journal, "Target")
    transfer_id, outgoing_id, incoming_id = move(journal, source, target, "30", START + timedelta(days=1))
    journal.m_service.set_default_trading_account(target)
    assert journal.m_service.archive_trading_account(source)

    with pytest.raises(ValueError, match="archived"):
        journal.m_service.delete_account_transfer(transfer_id)

    with pytest.raises(ValueError, match="archived"):
        journal.m_service.create_account_transaction(
            AccountTransaction(
                AccountTransactionType.DEPOSIT,
                START + timedelta(days=2),
                Decimal("10"),
                account_id=source,
            )
        )

    assert journal.m_repository.get_account_transaction(outgoing_id) is not None
    assert journal.m_repository.get_account_transaction(incoming_id) is not None
    assert_transaction_closed(journal)


def test_rejected_transfer_edit_keeps_both_legs_and_parent(journal):
    """Historical transfer corrections must never produce partial ledger writes."""
    source = account(journal, "Source", opening="100")
    target = account(journal, "Target")
    transfer_id, outgoing_id, incoming_id = move(journal, source, target, "70", START + timedelta(days=1))
    proposal = AccountTransfer(
        source_account_id=source,
        destination_account_id=target,
        amount=Decimal("130"),
        occurred_at=START + timedelta(days=1),
        transfer_id=transfer_id,
    )

    with pytest.raises(ValueError, match="Insufficient"):
        journal.m_service.update_account_transfer(proposal)

    for leg_id in (outgoing_id, incoming_id):
        assert journal.m_repository.get_account_transaction(leg_id).amount == Decimal("70")

    row = journal.m_connection.execute(
        "SELECT amount FROM account_transfers WHERE transfer_id = ?",
        (transfer_id,),
    ).fetchone()
    assert Decimal(row["amount"]) == Decimal("70")
    assert_transaction_closed(journal)
