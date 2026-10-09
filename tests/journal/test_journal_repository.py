# =============================================================================
# File: test_journal_repository.py
# Purpose: Pytest file for test_journal_repository.py.
# =============================================================================

import sqlite3
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from stonks.journal.account_transaction import AccountTransaction
from stonks.journal.account_transaction_type import AccountTransactionType
from stonks.journal.execution_side import ExecutionSide
from stonks.journal.journal_database import (
    create_connection,
    initialize_database,
)
from stonks.journal.journal_repository import (
    JournalRepository,
)
from stonks.journal.position import Position
from stonks.journal.trade_execution import TradeExecution


@pytest.fixture
def repository(tmp_path: Path):
    """Provide a repository backed by a temporary database."""

    database_path = tmp_path / "test_journal.db"

    initialize_database(database_path)

    connection = create_connection(database_path)

    try:
        yield JournalRepository(connection)
    finally:
        connection.close()


def create_test_position() -> Position:
    """Construct a representative trading position."""

    return Position(
        ticker="NVDA",
        strategy="Momentum",
        catalyst="Positive earnings",
        entry_reason="Breakout confirmation",
    )


def create_test_execution(
    position_id: int,
    side: ExecutionSide = ExecutionSide.BUY,
    shares: Decimal = Decimal("10"),
) -> TradeExecution:
    """Construct a representative trade execution."""

    return TradeExecution(
        position_id=position_id,
        side=side,
        executed_at=datetime(
            2026,
            9,
            30,
            13,
            30,
            tzinfo=timezone.utc,
        ),
        shares=shares,
        price=Decimal("12.3456"),
        fees=Decimal("0.25"),
    )


def create_test_account_transaction(
    transaction_type: AccountTransactionType = (AccountTransactionType.DEPOSIT),
    amount: Decimal = Decimal("100.00"),
) -> AccountTransaction:
    """Construct a representative account transaction."""

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
        notes="Test account transaction",
    )


def test_create_position(repository) -> None:
    """Verify positions receive database identifiers."""

    position = create_test_position()

    with repository.m_connection:
        position_id = repository.create_position(position)

    assert position_id == 1


def test_get_position(repository) -> None:
    """Verify positions can be reconstructed from storage."""

    position = create_test_position()

    with repository.m_connection:
        position_id = repository.create_position(position)

    loaded = repository.get_position(position_id)

    assert loaded is not None
    assert loaded.position_id == position_id
    assert loaded.ticker == "NVDA"
    assert loaded.strategy == "Momentum"
    assert loaded.catalyst == "Positive earnings"


def test_get_positions(repository: JournalRepository) -> None:
    """Verify all positions are retrieved in database identifier order."""

    with repository.m_connection:
        first_id = repository.create_position(
            Position(
                ticker="NVDA",
                strategy="Momentum",
                catalyst="Positive earnings",
                entry_reason="Breakout confirmation",
            )
        )

        second_id = repository.create_position(
            Position(
                ticker="AMD",
                strategy="Reversal",
                catalyst="Analyst upgrade",
                entry_reason="Support bounce",
            )
        )

    positions = repository.get_positions()

    assert len(positions) == 2
    assert [position.position_id for position in positions] == [
        first_id,
        second_id,
    ]
    assert [position.ticker for position in positions] == [
        "NVDA",
        "AMD",
    ]


def test_get_positions_empty(repository: JournalRepository) -> None:
    """Verify retrieving positions from an empty database returns a list."""

    assert repository.get_positions() == []


def test_get_missing_position(repository) -> None:
    """Verify missing positions return None."""

    assert repository.get_position(999) is None


def test_update_position(repository) -> None:
    """Verify persisted position annotations can be updated."""

    position = create_test_position()

    with repository.m_connection:
        position_id = repository.create_position(position)

    position.position_id = position_id
    position.notes = "Followed the trading plan."

    with repository.m_connection:
        updated = repository.update_position(position)

    loaded = repository.get_position(position_id)

    assert updated is True
    assert loaded is not None
    assert loaded.notes == "Followed the trading plan."


def test_update_missing_position(repository) -> None:
    """Verify updates require a valid existing record."""

    position = create_test_position()
    position.position_id = 999

    with repository.m_connection:
        updated = repository.update_position(position)

    assert updated is False


def test_update_without_id(repository) -> None:
    """Verify unsaved positions cannot be updated."""

    position = create_test_position()

    with pytest.raises(ValueError):
        repository.update_position(position)


def test_delete_position(repository) -> None:
    """Verify positions can be deleted."""

    position = create_test_position()

    with repository.m_connection:
        position_id = repository.create_position(position)

    with repository.m_connection:
        deleted = repository.delete_position(position_id)

    assert deleted is True
    assert repository.get_position(position_id) is None


def test_delete_missing_position(repository) -> None:
    """Verify deleting missing records returns False."""

    with repository.m_connection:
        deleted = repository.delete_position(999)

    assert deleted is False


def test_create_and_get_execution(repository) -> None:
    """Verify executions persist with decimal precision."""

    with repository.m_connection:
        position_id = repository.create_position(create_test_position())

        execution_id = repository.create_execution(create_test_execution(position_id))

    loaded = repository.get_execution(execution_id)

    assert loaded is not None
    assert loaded.execution_id == execution_id
    assert loaded.position_id == position_id
    assert loaded.side == ExecutionSide.BUY
    assert loaded.shares == Decimal("10")
    assert loaded.price == Decimal("12.3456")
    assert loaded.fees == Decimal("0.25")


def test_get_missing_execution(repository) -> None:
    """Verify missing executions return None."""

    assert repository.get_execution(999) is None


def test_get_position_executions(repository) -> None:
    """Verify executions are returned chronologically."""

    with repository.m_connection:
        position_id = repository.create_position(create_test_position())

        later = create_test_execution(
            position_id,
            ExecutionSide.SELL,
            shares=Decimal("5"),
        )
        later.executed_at = datetime(
            2026,
            9,
            30,
            14,
            0,
            tzinfo=timezone.utc,
        )

        earlier = create_test_execution(
            position_id,
            ExecutionSide.BUY,
            shares=Decimal("10"),
        )

        repository.create_execution(later)
        repository.create_execution(earlier)

    executions = repository.get_position_executions(position_id)

    assert len(executions) == 2
    assert executions[0].side == ExecutionSide.BUY
    assert executions[1].side == ExecutionSide.SELL


def test_get_executions(repository: JournalRepository) -> None:
    """Verify all executions are retrieved chronologically across positions."""

    with repository.m_connection:
        first_position_id = repository.create_position(
            Position(
                ticker="NVDA",
                strategy="Momentum",
                catalyst="Positive earnings",
                entry_reason="Breakout confirmation",
            )
        )

        second_position_id = repository.create_position(
            Position(
                ticker="AMD",
                strategy="Reversal",
                catalyst="Analyst upgrade",
                entry_reason="Support bounce",
            )
        )

        later_id = repository.create_execution(
            TradeExecution(
                position_id=first_position_id,
                side=ExecutionSide.SELL,
                executed_at=datetime(2026, 10, 8, 16, 0, tzinfo=timezone.utc),
                shares=Decimal("5"),
                price=Decimal("120"),
            )
        )

        earlier_id = repository.create_execution(
            TradeExecution(
                position_id=second_position_id,
                side=ExecutionSide.BUY,
                executed_at=datetime(2026, 10, 8, 14, 0, tzinfo=timezone.utc),
                shares=Decimal("10"),
                price=Decimal("50"),
            )
        )

    executions = repository.get_executions()

    assert len(executions) == 2

    assert [execution.execution_id for execution in executions] == [
        earlier_id,
        later_id,
    ]

    assert [execution.position_id for execution in executions] == [
        second_position_id,
        first_position_id,
    ]


def test_get_executions_empty(repository: JournalRepository) -> None:
    """Verify retrieving executions from an empty database returns a list."""

    assert repository.get_executions() == []


def test_update_execution(repository) -> None:
    """Verify an existing execution can be updated."""

    with repository.m_connection:
        position_id = repository.create_position(create_test_position())

        execution = create_test_execution(position_id)

        execution_id = repository.create_execution(execution)

    execution.execution_id = execution_id
    execution.shares = Decimal("15")
    execution.notes = "Added shares on breakout."

    with repository.m_connection:
        updated = repository.update_execution(execution)

    loaded = repository.get_execution(execution_id)

    assert updated is True
    assert loaded is not None
    assert loaded.shares == Decimal("15")
    assert loaded.notes == "Added shares on breakout."


def test_update_execution_without_id(repository) -> None:
    """Verify unsaved executions cannot be updated."""

    execution = create_test_execution(position_id=1)

    with pytest.raises(ValueError):
        repository.update_execution(execution)


def test_delete_execution(repository) -> None:
    """Verify executions can be deleted."""

    with repository.m_connection:
        position_id = repository.create_position(create_test_position())

        execution_id = repository.create_execution(create_test_execution(position_id))

    with repository.m_connection:
        deleted = repository.delete_execution(execution_id)

    assert deleted is True
    assert repository.get_execution(execution_id) is None


def test_execution_foreign_key(repository) -> None:
    """Verify executions require an existing position."""

    execution = create_test_execution(position_id=999)

    with pytest.raises(sqlite3.IntegrityError):
        with repository.m_connection:
            repository.create_execution(execution)


def test_position_cascade_delete(repository) -> None:
    """Verify deleting a position removes its executions."""

    with repository.m_connection:
        position_id = repository.create_position(create_test_position())

        execution_id = repository.create_execution(create_test_execution(position_id))

    with repository.m_connection:
        repository.delete_position(position_id)

    assert repository.get_position(position_id) is None
    assert repository.get_execution(execution_id) is None


def test_create_and_get_account_transaction(repository) -> None:
    """Verify account transactions persist correctly."""

    transaction = create_test_account_transaction()

    with repository.m_connection:
        transaction_id = repository.create_account_transaction(transaction)

    loaded = repository.get_account_transaction(transaction_id)

    assert loaded is not None
    assert loaded.transaction_id == transaction_id
    assert loaded.transaction_type == AccountTransactionType.DEPOSIT
    assert loaded.amount == Decimal("100.00")
    assert loaded.occurred_at == transaction.occurred_at
    assert loaded.notes == "Test account transaction"


def test_get_missing_account_transaction(repository) -> None:
    """Verify missing transactions return None."""

    assert repository.get_account_transaction(999) is None


def test_get_account_transactions(repository) -> None:
    """Verify account transactions are ordered chronologically."""

    later = create_test_account_transaction(
        AccountTransactionType.WITHDRAWAL,
        Decimal("25.00"),
    )
    later.occurred_at = datetime(2026, 9, 30, 14, 0, tzinfo=timezone.utc)

    earlier = create_test_account_transaction(
        AccountTransactionType.DEPOSIT,
        Decimal("100.00"),
    )

    with repository.m_connection:
        repository.create_account_transaction(later)
        repository.create_account_transaction(earlier)

    transactions = repository.get_account_transactions()

    assert len(transactions) == 2
    assert transactions[0].transaction_type == (AccountTransactionType.DEPOSIT)
    assert transactions[1].transaction_type == (AccountTransactionType.WITHDRAWAL)


def test_update_account_transaction(repository) -> None:
    """Verify account transactions can be updated."""

    transaction = create_test_account_transaction()

    with repository.m_connection:
        transaction_id = repository.create_account_transaction(transaction)

    transaction.transaction_id = transaction_id
    transaction.amount = Decimal("150.75")
    transaction.notes = "Corrected deposit amount"

    with repository.m_connection:
        updated = repository.update_account_transaction(transaction)

    loaded = repository.get_account_transaction(transaction_id)

    assert updated is True
    assert loaded is not None
    assert loaded.amount == Decimal("150.75")
    assert loaded.notes == "Corrected deposit amount"


def test_update_account_transaction_without_id(repository) -> None:
    """Verify unsaved transactions cannot be updated."""

    transaction = create_test_account_transaction()

    with pytest.raises(ValueError):
        repository.update_account_transaction(transaction)


def test_delete_account_transaction(repository) -> None:
    """Verify account transactions can be deleted."""

    with repository.m_connection:
        transaction_id = repository.create_account_transaction(create_test_account_transaction())

    with repository.m_connection:
        deleted = repository.delete_account_transaction(transaction_id)

    assert deleted is True
    assert repository.get_account_transaction(transaction_id) is None


def test_delete_missing_account_transaction(repository) -> None:
    """Verify deleting missing transactions returns False."""

    with repository.m_connection:
        deleted = repository.delete_account_transaction(999)

    assert deleted is False


def test_account_transaction_decimal_precision(repository) -> None:
    """Verify monetary precision survives a database round trip."""

    transaction = create_test_account_transaction(
        AccountTransactionType.ADJUSTMENT,
        Decimal("-12.3456"),
    )

    with repository.m_connection:
        transaction_id = repository.create_account_transaction(transaction)

    loaded = repository.get_account_transaction(transaction_id)

    assert loaded is not None
    assert loaded.amount == Decimal("-12.3456")


def test_account_transaction_invalid_type(repository) -> None:
    """Verify SQLite rejects unsupported transaction types."""

    with pytest.raises(sqlite3.IntegrityError):
        with repository.m_connection:
            repository.m_connection.execute(
                """
                INSERT INTO account_transactions (
                    transaction_type,
                    occurred_at,
                    amount
                )
                VALUES (?, ?, ?)
                """,
                (
                    "INVALID",
                    "2026-09-30T13:30:00+00:00",
                    "100.00",
                ),
            )


def test_fractional_share_execution(repository) -> None:
    """Verify fractional shares survive database persistence."""

    with repository.m_connection:
        position_id = repository.create_position(create_test_position())

        execution = create_test_execution(
            position_id=position_id,
            shares=Decimal("1.375"),
        )

        execution_id = repository.create_execution(execution)

    loaded = repository.get_execution(execution_id)

    assert loaded is not None
    assert loaded.shares == Decimal("1.375")
    assert loaded.price == Decimal("12.3456")
    assert loaded.gross_value == Decimal("16.9752")
