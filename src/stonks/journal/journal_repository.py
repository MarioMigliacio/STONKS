# =============================================================================
# File: journal_repository.py
# Purpose: Provides SQLite persistence for journal entities.
# =============================================================================

import sqlite3
from datetime import datetime
from decimal import Decimal
from typing import Optional

from stonks.journal.account_transaction import AccountTransaction
from stonks.journal.account_transaction_type import AccountTransactionType
from stonks.journal.execution_side import ExecutionSide
from stonks.journal.position import Position
from stonks.journal.trade_execution import TradeExecution


class JournalRepository:
    """
    Provides database CRUD operations for journal entities.

    Uses a caller-managed SQLite connection. Transaction
    boundaries and commits are owned by the caller.

    Attributes:
        m_connection:
            Active SQLite database connection.
    """

    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        """
        Initialize the journal repository.

        Args:
            connection:
                Active SQLite database connection.
        """
        self.m_connection = connection

    def create_position(
        self,
        position: Position,
    ) -> int:
        """
        Insert a new trading position.

        Args:
            position:
                Position to persist.

        Returns:
            int:
                Newly generated database identifier.
        """
        cursor = self.m_connection.execute(
            """
            INSERT INTO positions (
                ticker,
                strategy,
                catalyst,
                entry_reason,
                exit_reason,
                mistakes,
                lessons_learned,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                position.ticker,
                position.strategy,
                position.catalyst,
                position.entry_reason,
                position.exit_reason,
                position.mistakes,
                position.lessons_learned,
                position.notes,
            ),
        )

        if cursor.lastrowid is None:
            raise RuntimeError("Failed to retrieve the new position ID.")

        return cursor.lastrowid

    def get_position(
        self,
        position_id: int,
    ) -> Optional[Position]:
        """
        Retrieve a trading position by identifier.

        Args:
            position_id:
                Database identifier to retrieve.

        Returns:
            Optional[Position]:
                Position if found, otherwise None.
        """
        row = self.m_connection.execute(
            """
            SELECT *
            FROM positions
            WHERE position_id = ?
            """,
            (position_id,),
        ).fetchone()

        if row is None:
            return None

        return self._row_to_position(row)

    def update_position(
        self,
        position: Position,
    ) -> bool:
        """
        Update an existing trading position.

        Args:
            position:
                Position containing updated values.

        Returns:
            bool:
                True if a record was updated.
        """
        if position.position_id is None:
            raise ValueError("Cannot update a position without an ID.")

        cursor = self.m_connection.execute(
            """
            UPDATE positions
            SET
                ticker = ?,
                strategy = ?,
                catalyst = ?,
                entry_reason = ?,
                exit_reason = ?,
                mistakes = ?,
                lessons_learned = ?,
                notes = ?
            WHERE position_id = ?
            """,
            (
                position.ticker,
                position.strategy,
                position.catalyst,
                position.entry_reason,
                position.exit_reason,
                position.mistakes,
                position.lessons_learned,
                position.notes,
                position.position_id,
            ),
        )

        return cursor.rowcount > 0

    def delete_position(
        self,
        position_id: int,
    ) -> bool:
        """
        Delete a position and its related executions.

        Associated executions are deleted through the
        database's ON DELETE CASCADE constraint.

        Args:
            position_id:
                Identifier of the position to delete.

        Returns:
            bool:
                True if a record was deleted.
        """
        cursor = self.m_connection.execute(
            """
            DELETE FROM positions
            WHERE position_id = ?
            """,
            (position_id,),
        )

        return cursor.rowcount > 0

    @staticmethod
    def _row_to_position(
        row: sqlite3.Row,
    ) -> Position:
        """
        Convert a database row into a Position instance.

        Args:
            row:
                SQLite position record.

        Returns:
            Position:
                Reconstructed position entity.
        """
        return Position(
            position_id=row["position_id"],
            ticker=row["ticker"],
            strategy=row["strategy"],
            catalyst=row["catalyst"],
            entry_reason=row["entry_reason"],
            exit_reason=row["exit_reason"],
            mistakes=row["mistakes"],
            lessons_learned=row["lessons_learned"],
            notes=row["notes"],
        )

    def create_execution(
        self,
        execution: TradeExecution,
    ) -> int:
        """
        Insert a trade execution into the journal.

        Args:
            execution:
                Execution to persist.

        Returns:
            int:
                Newly generated execution identifier.
        """
        cursor = self.m_connection.execute(
            """
            INSERT INTO trade_executions (
                position_id,
                side,
                executed_at,
                shares,
                price,
                fees,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                execution.position_id,
                execution.side.value,
                execution.executed_at.isoformat(),
                execution.shares,
                str(execution.price),
                str(execution.fees),
                execution.notes,
            ),
        )

        if cursor.lastrowid is None:
            raise RuntimeError("Failed to retrieve the new execution ID.")

        return cursor.lastrowid

    def get_execution(
        self,
        execution_id: int,
    ) -> Optional[TradeExecution]:
        """
        Retrieve an execution by its identifier.

        Args:
            execution_id:
                Database execution identifier.

        Returns:
            Optional[TradeExecution]:
                Execution if found, otherwise None.
        """
        row = self.m_connection.execute(
            """
            SELECT *
            FROM trade_executions
            WHERE execution_id = ?
            """,
            (execution_id,),
        ).fetchone()

        if row is None:
            return None

        return self._row_to_execution(row)

    def get_position_executions(
        self,
        position_id: int,
    ) -> list[TradeExecution]:
        """
        Retrieve executions belonging to a position.

        Results are ordered chronologically, with execution
        identifiers breaking timestamp ties.

        Args:
            position_id:
                Identifier of the parent position.

        Returns:
            list[TradeExecution]:
                Chronologically ordered executions.
        """
        rows = self.m_connection.execute(
            """
            SELECT *
            FROM trade_executions
            WHERE position_id = ?
            ORDER BY executed_at ASC, execution_id ASC
            """,
            (position_id,),
        ).fetchall()

        return [self._row_to_execution(row) for row in rows]

    def update_execution(
        self,
        execution: TradeExecution,
    ) -> bool:
        """
        Update an existing trade execution.

        Args:
            execution:
                Execution containing updated values.

        Returns:
            bool:
                True if the record was updated.
        """
        if execution.execution_id is None:
            raise ValueError("Cannot update an execution without an ID.")

        cursor = self.m_connection.execute(
            """
            UPDATE trade_executions
            SET
                position_id = ?,
                side = ?,
                executed_at = ?,
                shares = ?,
                price = ?,
                fees = ?,
                notes = ?
            WHERE execution_id = ?
            """,
            (
                execution.position_id,
                execution.side.value,
                execution.executed_at.isoformat(),
                execution.shares,
                str(execution.price),
                str(execution.fees),
                execution.notes,
                execution.execution_id,
            ),
        )

        return cursor.rowcount > 0

    def delete_execution(
        self,
        execution_id: int,
    ) -> bool:
        """
        Delete a trade execution.

        Args:
            execution_id:
                Identifier of the execution to delete.

        Returns:
            bool:
                True if a record was deleted.
        """
        cursor = self.m_connection.execute(
            """
            DELETE FROM trade_executions
            WHERE execution_id = ?
            """,
            (execution_id,),
        )

        return cursor.rowcount > 0

    @staticmethod
    def _row_to_execution(
        row: sqlite3.Row,
    ) -> TradeExecution:
        """
        Convert a SQLite row into a TradeExecution.

        Args:
            row:
                SQLite execution record.

        Returns:
            TradeExecution:
                Reconstructed execution entity.
        """
        return TradeExecution(
            execution_id=row["execution_id"],
            position_id=row["position_id"],
            side=ExecutionSide(row["side"]),
            executed_at=datetime.fromisoformat(row["executed_at"]),
            shares=row["shares"],
            price=Decimal(row["price"]),
            fees=Decimal(row["fees"]),
            notes=row["notes"],
        )

    def create_account_transaction(
        self,
        transaction: AccountTransaction,
    ) -> int:
        """
        Insert an account transaction.

        Args:
            transaction:
                Account transaction to persist.

        Returns:
            int:
                Newly generated transaction identifier.
        """
        cursor = self.m_connection.execute(
            """
            INSERT INTO account_transactions (
                transaction_type,
                occurred_at,
                amount,
                notes
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                transaction.transaction_type.value,
                transaction.occurred_at.isoformat(),
                str(transaction.amount),
                transaction.notes,
            ),
        )

        if cursor.lastrowid is None:
            raise RuntimeError("Failed to retrieve the new transaction ID.")

        return cursor.lastrowid

    def get_account_transaction(
        self,
        transaction_id: int,
    ) -> Optional[AccountTransaction]:
        """
        Retrieve an account transaction by identifier.

        Args:
            transaction_id:
                Database transaction identifier.

        Returns:
            Optional[AccountTransaction]:
                Transaction if found, otherwise None.
        """
        row = self.m_connection.execute(
            """
            SELECT *
            FROM account_transactions
            WHERE transaction_id = ?
            """,
            (transaction_id,),
        ).fetchone()

        if row is None:
            return None

        return self._row_to_account_transaction(row)

    def get_account_transactions(
        self,
    ) -> list[AccountTransaction]:
        """
        Retrieve all account transactions chronologically.

        Returns:
            list[AccountTransaction]:
                Transactions ordered by timestamp and ID.
        """
        rows = self.m_connection.execute(
            """
            SELECT *
            FROM account_transactions
            ORDER BY occurred_at ASC, transaction_id ASC
            """
        ).fetchall()

        return [self._row_to_account_transaction(row) for row in rows]

    def update_account_transaction(
        self,
        transaction: AccountTransaction,
    ) -> bool:
        """
        Update an existing account transaction.

        Args:
            transaction:
                Transaction containing updated values.

        Returns:
            bool:
                True if a record was updated.
        """
        if transaction.transaction_id is None:
            raise ValueError("Cannot update a transaction without an ID.")

        cursor = self.m_connection.execute(
            """
            UPDATE account_transactions
            SET
                transaction_type = ?,
                occurred_at = ?,
                amount = ?,
                notes = ?
            WHERE transaction_id = ?
            """,
            (
                transaction.transaction_type.value,
                transaction.occurred_at.isoformat(),
                str(transaction.amount),
                transaction.notes,
                transaction.transaction_id,
            ),
        )

        return cursor.rowcount > 0

    def delete_account_transaction(
        self,
        transaction_id: int,
    ) -> bool:
        """
        Delete an account transaction.

        Args:
            transaction_id:
                Identifier of the transaction to delete.

        Returns:
            bool:
                True if a record was deleted.
        """
        cursor = self.m_connection.execute(
            """
            DELETE FROM account_transactions
            WHERE transaction_id = ?
            """,
            (transaction_id,),
        )

        return cursor.rowcount > 0

    @staticmethod
    def _row_to_account_transaction(
        row: sqlite3.Row,
    ) -> AccountTransaction:
        """
        Convert a SQLite row into an AccountTransaction.

        Args:
            row:
                SQLite account transaction record.

        Returns:
            AccountTransaction:
                Reconstructed account transaction.
        """
        return AccountTransaction(
            transaction_id=row["transaction_id"],
            transaction_type=AccountTransactionType(row["transaction_type"]),
            occurred_at=datetime.fromisoformat(row["occurred_at"]),
            amount=Decimal(row["amount"]),
            notes=row["notes"],
        )
