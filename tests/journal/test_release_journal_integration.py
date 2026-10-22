# =============================================================================
# File: test_release_journal_integration.py
# Purpose: Validate end-to-end persisted journal cash and performance workflows.
# =============================================================================

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from stonks.journal.analytics.account_analytics import calculate_account_metrics
from stonks.journal.analytics.position_analytics import calculate_position_metrics
from stonks.journal.journal_context import JournalContext
from stonks.journal.models.account_transaction import AccountTransaction
from stonks.journal.models.account_transaction_type import AccountTransactionType
from stonks.journal.models.account_type import AccountType
from stonks.journal.models.execution_side import ExecutionSide
from stonks.journal.models.opening_cash_balance import OpeningCashBalance
from stonks.journal.models.position import Position
from stonks.journal.models.trade_execution import TradeExecution
from stonks.journal.models.trading_account import TradingAccount
from stonks.journal.persistence.opening_cash_repository import OpeningCashRepository

START = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)


def _transaction(context, account_id, kind, amount, day):
    """Persist an account cash movement through its public service."""
    return context.m_service.create_account_transaction(
        AccountTransaction(
            transaction_type=kind,
            occurred_at=START + timedelta(days=day),
            amount=Decimal(amount),
            account_id=account_id,
        )
    )


def _execution(context, position_id, side, shares, price, day, fees="0"):
    """Persist a dated trade execution through its public service."""
    return context.m_service.create_execution(
        TradeExecution(
            position_id=position_id,
            side=side,
            executed_at=START + timedelta(days=day),
            shares=Decimal(shares),
            price=Decimal(price),
            fees=Decimal(fees),
        )
    )


def _metrics(context, account_id):
    """Calculate account metrics from persisted records, as Account Details does."""
    transactions = context.m_repository.get_account_transactions(account_id)
    positions = context.m_repository.get_positions(account_id=account_id)
    executions = []
    position_metrics = []

    for position in positions:
        fills = context.m_repository.get_position_executions(position.position_id)
        executions.extend(fills)
        position_metrics.append(calculate_position_metrics(position.position_id, fills))

    opening = OpeningCashRepository(context.m_connection).get(account_id)

    return calculate_account_metrics(transactions, executions, position_metrics, opening)


def _build_journal(context):
    """Populate two accounts with real contributions, fills, and linked transfers."""
    source = context.m_service.create_trading_account(TradingAccount("Cash", AccountType.CASH))
    destination = context.m_service.create_trading_account(TradingAccount("Roth", AccountType.ROTH_IRA))

    context.m_service.set_opening_cash(OpeningCashBalance(source, Decimal("1000"), START))
    context.m_service.set_opening_cash(OpeningCashBalance(destination, Decimal("100"), START))

    _transaction(context, source, AccountTransactionType.DEPOSIT, "200", 1)
    position_id = context.m_service.create_position(Position("NVDA", account_id=source))
    _execution(context, position_id, ExecutionSide.BUY, "2", "100", 2, fees="2")
    _execution(context, position_id, ExecutionSide.SELL, "1", "150", 3, fees="1")
    context.m_service.create_account_transfer(
        source,
        destination,
        Decimal("250"),
        START + timedelta(days=4),
        "Release integration allocation",
    )
    _transaction(context, source, AccountTransactionType.FEE, "10", 5)

    return source, destination, position_id


def test_complete_journal_lifecycle_financial_reconciliation(tmp_path):
    """Contributions, fees, transfers, and fills reconcile across two accounts."""
    with JournalContext(tmp_path / "lifecycle.db") as context:
        source, destination, position_id = _build_journal(context)

        sending = _metrics(context, source)
        receiving = _metrics(context, destination)
        position = calculate_position_metrics(
            position_id,
            context.m_repository.get_position_executions(position_id),
        )

        assert sending.cash_balance == Decimal("887")
        assert sending.total_deposits == Decimal("200")
        assert sending.net_contributions == Decimal("200")
        assert sending.realized_trading_pnl == Decimal("48")
        assert sending.account_fees == Decimal("10")
        assert sending.net_realized_pnl == Decimal("38")
        assert sending.open_position_cost_basis == Decimal("101")
        assert sending.equity_at_cost_basis == Decimal("988")

        assert receiving.cash_balance == Decimal("350")
        assert receiving.net_contributions == Decimal("0")
        assert receiving.net_realized_pnl == Decimal("0")
        assert position.open_shares == Decimal("1")
        assert position.remaining_cost_basis == Decimal("101")

        transfer_legs = [
            item for item in context.m_repository.get_account_transactions() if item.transfer_id is not None
        ]
        assert len(transfer_legs) == 2
        assert transfer_legs[0].transfer_id == transfer_legs[1].transfer_id
        assert sum((leg.net_cash_flow for leg in transfer_legs), Decimal("0")) == 0
        assert sending.cash_balance + receiving.cash_balance == Decimal("1237")


def test_reopening_existing_database_preserves_financial_state(tmp_path):
    """The initialization path must preserve v3 history across application sessions."""
    db_path = tmp_path / "reopen.db"

    with JournalContext(db_path) as context:
        source, destination, _ = _build_journal(context)
        expected = (_metrics(context, source), _metrics(context, destination))

    with JournalContext(db_path) as reopened:
        assert _metrics(reopened, source) == expected[0]
        assert _metrics(reopened, destination) == expected[1]
        assert len(reopened.m_repository.get_positions(source)) == 1
        assert len(reopened.m_repository.get_account_transactions()) == 4
        assert reopened.m_connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert not reopened.m_connection.in_transaction


def test_rejected_overdraft_keeps_complete_journal_unchanged(tmp_path):
    """A rejected cash mutation must leave the persisted positions and transfer pair intact."""
    with JournalContext(tmp_path / "rollback.db") as context:
        source, destination, position_id = _build_journal(context)
        original_source = _metrics(context, source)
        original_destination = _metrics(context, destination)
        original_fills = context.m_repository.get_position_executions(position_id)

        with pytest.raises(ValueError, match="Insufficient"):
            _transaction(context, source, AccountTransactionType.WITHDRAWAL, "1000", 6)

        assert _metrics(context, source) == original_source
        assert _metrics(context, destination) == original_destination
        assert context.m_repository.get_position_executions(position_id) == original_fills
        assert context.m_connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert not context.m_connection.in_transaction


def test_archived_account_retains_history_but_rejects_new_writes(tmp_path):
    """Archiving preserves readable account history without permitting new spending."""
    with JournalContext(tmp_path / "archived.db") as context:
        source, destination, _ = _build_journal(context)
        original = _metrics(context, source)

        context.m_service.set_default_trading_account(destination)
        assert context.m_service.archive_trading_account(source)

        with pytest.raises(ValueError, match="archived"):
            _transaction(context, source, AccountTransactionType.WITHDRAWAL, "1", 6)

        assert _metrics(context, source) == original
        assert not context.m_repository.get_trading_account(source).is_active
        assert not context.m_connection.in_transaction
