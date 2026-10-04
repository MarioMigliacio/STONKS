# =============================================================================
# File: journal_service.py
# Purpose: Enforce journal business rules and transaction integrity.
# =============================================================================

import sqlite3
from decimal import Decimal

from stonks.journal.account_transaction import AccountTransaction
from stonks.journal.execution_side import ExecutionSide
from stonks.journal.journal_repository import JournalRepository
from stonks.journal.journal_validation import (
    normalize_timestamp,
    validate_account_transaction,
    validate_execution,
)
from stonks.journal.trade_execution import TradeExecution


class JournalService:
    """
    Coordinate journal persistence and trading business rules.

    Attributes:
        m_connection:
            SQLite connection used for atomic transactions.

        m_repository:
            Repository responsible for journal persistence.
    """

    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.m_connection = connection
        self.m_repository = JournalRepository(connection)

    def validate_position_history(
        self,
        position_id: int,
    ) -> None:
        """
        Validate the chronological execution history.

        Rejects overselling, selling before buying, and
        reopening a position after its balance reaches zero.

        Args:
            position_id:
                Position whose executions must be checked.

        Raises:
            ValueError:
                If an execution violates position integrity.
        """
        executions = self.m_repository.get_position_executions(position_id)

        # Normalize in memory before sorting. This also
        # protects against legacy offset-aware timestamps.
        executions.sort(
            key=lambda execution: (
                normalize_timestamp(execution.executed_at),
                execution.execution_id,
            )
        )

        balance = Decimal("0")
        has_opened = False
        has_closed = False

        for execution in executions:
            validate_execution(execution)

            if execution.side == ExecutionSide.BUY:
                if has_closed:
                    raise ValueError("A closed position cannot be reopened.")

                balance += execution.shares
                has_opened = True

            elif execution.side == ExecutionSide.SELL:
                if not has_opened:
                    raise ValueError("Cannot sell before opening a position.")

                balance -= execution.shares

                if balance < 0:
                    raise ValueError("Execution exceeds available shares.")

                if balance == 0:
                    has_closed = True

    def create_execution(
        self,
        execution: TradeExecution,
    ) -> int:
        """
        Create an execution if the resulting history is valid.

        Args:
            execution:
                Trade execution to persist.

        Returns:
            int:
                Identifier of the created execution.

        Raises:
            ValueError:
                If the execution violates trading rules.
        """
        validate_execution(execution)

        # Avoid mutating the caller's execution.
        normalized = TradeExecution(
            position_id=execution.position_id,
            side=execution.side,
            executed_at=normalize_timestamp(execution.executed_at),
            shares=execution.shares,
            price=execution.price,
            execution_id=None,
            fees=execution.fees,
            notes=execution.notes,
        )

        if self.m_connection.in_transaction:
            raise RuntimeError("JournalService requires a connection without an active transaction.")

        # Acquire the write lock before inspecting history.
        self.m_connection.execute("BEGIN IMMEDIATE")

        try:
            if self.m_repository.get_position(normalized.position_id) is None:
                raise ValueError("Position does not exist.")

            execution_id = self.m_repository.create_execution(normalized)

            self.validate_position_history(normalized.position_id)

            self.m_connection.commit()

            return execution_id

        except Exception:
            self.m_connection.rollback()
            raise

    def update_execution(
        self,
        execution: TradeExecution,
    ) -> bool:
        """
        Update an execution while preserving position integrity.

        Revalidates the complete execution history after the
        modification. Prevents moving executions between positions.

        Args:
            execution:
                Execution containing the updated values.

        Returns:
            bool:
                True if updated, False if the execution does
                not exist.

        Raises:
            ValueError:
                If the update violates trading rules.
        """
        if execution.execution_id is None:
            raise ValueError("Cannot update an execution without an ID.")

        validate_execution(execution)

        normalized = TradeExecution(
            position_id=execution.position_id,
            side=execution.side,
            executed_at=normalize_timestamp(execution.executed_at),
            shares=execution.shares,
            price=execution.price,
            execution_id=execution.execution_id,
            fees=execution.fees,
            notes=execution.notes,
        )

        if self.m_connection.in_transaction:
            raise RuntimeError("JournalService requires a connection without an active transaction.")

        self.m_connection.execute("BEGIN IMMEDIATE")

        try:
            existing = self.m_repository.get_execution(normalized.execution_id)

            if existing is None:
                self.m_connection.rollback()
                return False

            if existing.position_id != normalized.position_id:
                raise ValueError("Cannot move an execution to another position.")

            updated = self.m_repository.update_execution(normalized)

            self.validate_position_history(normalized.position_id)

            self.m_connection.commit()

            return updated

        except Exception:
            self.m_connection.rollback()
            raise

    def delete_execution(
        self,
        execution_id: int,
    ) -> bool:
        """
        Delete an execution if its position remains valid.

        Args:
            execution_id:
                Identifier of the execution to remove.

        Returns:
            bool:
                True if deleted, False if the execution
                does not exist.

        Raises:
            ValueError:
                If deletion invalidates position history.
        """
        if self.m_connection.in_transaction:
            raise RuntimeError("JournalService requires a connection without an active transaction.")

        self.m_connection.execute("BEGIN IMMEDIATE")

        try:
            existing = self.m_repository.get_execution(execution_id)

            if existing is None:
                self.m_connection.rollback()
                return False

            deleted = self.m_repository.delete_execution(execution_id)

            self.validate_position_history(existing.position_id)

            self.m_connection.commit()

            return deleted

        except Exception:
            self.m_connection.rollback()
            raise

    def create_account_transaction(
        self,
        transaction: AccountTransaction,
    ) -> int:
        """
        Validate and persist an account transaction.

        Args:
            transaction:
                Account transaction to create.

        Returns:
            int:
                Identifier of the new transaction.

        Raises:
            ValueError:
                If the transaction contains invalid data.
        """
        validate_account_transaction(transaction)

        normalized = AccountTransaction(
            transaction_type=transaction.transaction_type,
            occurred_at=normalize_timestamp(transaction.occurred_at),
            amount=transaction.amount,
            transaction_id=None,
            notes=transaction.notes,
        )

        if self.m_connection.in_transaction:
            raise RuntimeError("JournalService requires a connection without an active transaction.")

        self.m_connection.execute("BEGIN IMMEDIATE")

        try:
            transaction_id = self.m_repository.create_account_transaction(normalized)

            self.m_connection.commit()

            return transaction_id

        except Exception:
            self.m_connection.rollback()
            raise

    def update_account_transaction(
        self,
        transaction: AccountTransaction,
    ) -> bool:
        """
        Validate and update an existing account transaction.

        Args:
            transaction:
                Transaction containing corrected values.

        Returns:
            bool:
                True if updated, False if not found.

        Raises:
            ValueError:
                If the transaction contains invalid data.
        """
        if transaction.transaction_id is None:
            raise ValueError("Cannot update a transaction without an ID.")

        validate_account_transaction(transaction)

        normalized = AccountTransaction(
            transaction_type=transaction.transaction_type,
            occurred_at=normalize_timestamp(transaction.occurred_at),
            amount=transaction.amount,
            transaction_id=transaction.transaction_id,
            notes=transaction.notes,
        )

        if self.m_connection.in_transaction:
            raise RuntimeError("JournalService requires a connection without an active transaction.")

        self.m_connection.execute("BEGIN IMMEDIATE")

        try:
            existing = self.m_repository.get_account_transaction(normalized.transaction_id)

            if existing is None:
                self.m_connection.rollback()
                return False

            updated = self.m_repository.update_account_transaction(normalized)

            self.m_connection.commit()

            return updated

        except Exception:
            self.m_connection.rollback()
            raise

    def delete_account_transaction(
        self,
        transaction_id: int,
    ) -> bool:
        """
        Delete an account transaction atomically.

        Args:
            transaction_id:
                Identifier of the transaction to delete.

        Returns:
            bool:
                True if deleted, False if not found.
        """
        if self.m_connection.in_transaction:
            raise RuntimeError("JournalService requires a connection without an active transaction.")

        self.m_connection.execute("BEGIN IMMEDIATE")

        try:
            deleted = self.m_repository.delete_account_transaction(transaction_id)

            self.m_connection.commit()

            return deleted

        except Exception:
            self.m_connection.rollback()
            raise
