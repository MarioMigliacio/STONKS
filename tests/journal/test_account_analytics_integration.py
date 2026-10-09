# =============================================================================
# File: test_account_analytics_integration.py
# Purpose: Pytest file for test_account_analytics_integration.py.
# =============================================================================

from datetime import datetime, timezone
from decimal import Decimal

from stonks.journal.account_analytics import calculate_account_metrics
from stonks.journal.account_transaction import AccountTransaction
from stonks.journal.account_transaction_type import AccountTransactionType
from stonks.journal.execution_side import ExecutionSide
from stonks.journal.journal_database import (
    create_connection,
    initialize_database,
)
from stonks.journal.journal_repository import JournalRepository
from stonks.journal.journal_service import JournalService
from stonks.journal.position import Position
from stonks.journal.position_analytics import calculate_position_metrics
from stonks.journal.trade_execution import TradeExecution


def test_persisted_account_transactions(tmp_path) -> None:
    """
    Verify account metrics using transactions persisted in SQLite.
    """
    database_path = tmp_path / "journal.db"
    initialize_database(database_path)

    connection = create_connection(database_path)

    try:
        repository = JournalRepository(connection)
        service = JournalService(connection)

        occurred_at = datetime(2026, 10, 8, 14, 30, tzinfo=timezone.utc)

        transactions = [
            AccountTransaction(
                transaction_type=AccountTransactionType.DEPOSIT,
                occurred_at=occurred_at,
                amount=Decimal("1000.25"),
            ),
            AccountTransaction(
                transaction_type=AccountTransactionType.WITHDRAWAL,
                occurred_at=occurred_at,
                amount=Decimal("200"),
            ),
            AccountTransaction(
                transaction_type=AccountTransactionType.FEE,
                occurred_at=occurred_at,
                amount=Decimal("4.25"),
            ),
            AccountTransaction(
                transaction_type=AccountTransactionType.ADJUSTMENT,
                occurred_at=occurred_at,
                amount=Decimal("-10"),
            ),
        ]

        for transaction in transactions:
            service.create_account_transaction(transaction)

        persisted = repository.get_account_transactions()

        metrics = calculate_account_metrics(
            transactions=persisted,
            executions=[],
            positions=[],
        )

        assert metrics.total_deposits == Decimal("1000.25")
        assert metrics.total_withdrawals == Decimal("200")
        assert metrics.net_contributions == Decimal("800.25")

        assert metrics.cash_balance == Decimal("786.00")

        assert metrics.realized_trading_pnl == Decimal("0")
        assert metrics.account_fees == Decimal("4.25")
        assert metrics.net_realized_pnl == Decimal("-4.25")

        assert metrics.open_position_cost_basis == Decimal("0")
        assert metrics.equity_at_cost_basis == Decimal("786.00")

    finally:
        connection.close()


def test_persisted_account_reconciliation(tmp_path) -> None:
    """Verify persisted trading activity reconciles account equity."""

    database_path = tmp_path / "journal.db"
    initialize_database(database_path)

    connection = create_connection(database_path)

    try:
        repository = JournalRepository(connection)
        service = JournalService(connection)

        occurred_at = datetime(2026, 10, 8, 14, 30, tzinfo=timezone.utc)

        service.create_account_transaction(
            AccountTransaction(
                transaction_type=AccountTransactionType.DEPOSIT,
                occurred_at=occurred_at,
                amount=Decimal("2000"),
            )
        )

        service.create_account_transaction(
            AccountTransaction(
                transaction_type=AccountTransactionType.FEE,
                occurred_at=occurred_at,
                amount=Decimal("5"),
            )
        )

        service.create_account_transaction(
            AccountTransaction(
                transaction_type=AccountTransactionType.ADJUSTMENT,
                occurred_at=occurred_at,
                amount=Decimal("20"),
            )
        )

        position_id = service.create_position(
            Position(
                ticker="NVDA",
                strategy="Momentum",
                catalyst="Earnings",
                entry_reason="Breakout confirmation",
            )
        )

        service.create_execution(
            TradeExecution(
                position_id=position_id,
                side=ExecutionSide.BUY,
                executed_at=occurred_at,
                shares=Decimal("10"),
                price=Decimal("50"),
                fees=Decimal("2"),
            )
        )

        service.create_execution(
            TradeExecution(
                position_id=position_id,
                side=ExecutionSide.SELL,
                executed_at=occurred_at.replace(hour=15),
                shares=Decimal("5"),
                price=Decimal("60"),
                fees=Decimal("3"),
            )
        )

        transactions = repository.get_account_transactions()
        executions = repository.get_executions()

        positions = [
            calculate_position_metrics(
                position.position_id,
                repository.get_position_executions(position.position_id),
            )
            for position in repository.get_positions()
        ]

        metrics = calculate_account_metrics(
            transactions=transactions,
            executions=executions,
            positions=positions,
        )

        assert metrics.net_contributions == Decimal("2000")
        assert metrics.cash_balance == Decimal("1810")
        assert metrics.open_position_cost_basis == Decimal("251")
        assert metrics.realized_trading_pnl == Decimal("46")
        assert metrics.net_realized_pnl == Decimal("41")
        assert metrics.equity_at_cost_basis == Decimal("2061")

        assert metrics.equity_at_cost_basis == (metrics.net_contributions + metrics.net_realized_pnl + Decimal("20"))

    finally:
        connection.close()
