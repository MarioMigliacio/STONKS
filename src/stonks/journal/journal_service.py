# =============================================================================
# File: journal_service.py
# Purpose: Enforce journal business rules and transaction integrity.
# =============================================================================

import sqlite3
from contextlib import contextmanager
from dataclasses import replace
from decimal import Decimal
from typing import Generator

from stonks.journal.account_transaction import AccountTransaction
from stonks.journal.account_validation import validate_trading_account
from stonks.journal.execution_side import ExecutionSide
from stonks.journal.journal_repository import JournalRepository
from stonks.journal.journal_validation import (
    normalize_timestamp,
    validate_account_transaction,
    validate_execution,
    validate_position,
)
from stonks.journal.position import Position
from stonks.journal.trade_execution import TradeExecution
from stonks.journal.trading_account import TradingAccount


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

    @contextmanager
    def _transaction(self) -> Generator[None, None, None]:
        """
        Manage an atomic journal write transaction.

        Raises:
            RuntimeError:
                If the connection already has an active transaction.
        """
        if self.m_connection.in_transaction:
            raise RuntimeError("JournalService requires a connection without an active transaction.")

        self.m_connection.execute("BEGIN IMMEDIATE")

        try:
            yield
            self.m_connection.commit()

        except Exception:
            self.m_connection.rollback()
            raise

    def create_trading_account(
        self,
        account: TradingAccount,
    ) -> int:
        """
        Validate and create a trading account.

        The first account becomes the default automatically.

        Args:
            account:
                Trading account to create.

        Returns:
            int:
                Identifier of the new account.

        Raises:
            ValueError:
                If account data is invalid or the requested
                default account conflicts with an existing one.
        """
        validate_trading_account(account)

        with self._transaction():
            accounts = self.m_repository.get_trading_accounts()
            is_first_account = len(accounts) == 0

            normalized = replace(
                account,
                account_id=None,
                name=account.name.strip(),
                broker=account.broker.strip(),
                is_default=is_first_account or account.is_default,
            )

            validate_trading_account(normalized)

            if normalized.is_default:
                existing_default = self.m_repository.get_default_trading_account()

                if existing_default is not None:
                    raise ValueError("A default account already exists. Use set_default_trading_account() to switch.")

            return self.m_repository.create_trading_account(normalized)

    def update_trading_account(
        self,
        account: TradingAccount,
    ) -> bool:
        """
        Update account details without changing default selection.

        Args:
            account:
                Account containing updated information.

        Returns:
            bool:
                True if updated, False if not found.

        Raises:
            ValueError:
                If the update violates account rules.
        """
        if account.account_id is None:
            raise ValueError("Cannot update an account without an ID.")

        validate_trading_account(account)

        with self._transaction():
            existing = self.m_repository.get_trading_account(account.account_id)

            if existing is None:
                return False

            if account.is_default != existing.is_default:
                raise ValueError("Use set_default_trading_account() to change the default account.")

            if existing.is_default and not account.is_active:
                raise ValueError("Cannot archive the default account. Select another default first.")

            normalized = replace(
                account,
                name=account.name.strip(),
                broker=account.broker.strip(),
            )

            return self.m_repository.update_trading_account(normalized)

    def set_default_trading_account(
        self,
        account_id: int,
    ) -> None:
        """
        Atomically assign the default trading account.

        Args:
            account_id:
                Identifier of the account to select.

        Raises:
            ValueError:
                If the account does not exist or is archived.
        """
        with self._transaction():
            target = self.m_repository.get_trading_account(account_id)

            if target is None:
                raise ValueError("Trading account does not exist.")

            if not target.is_active:
                raise ValueError("Cannot make an archived account the default.")

            existing_default = self.m_repository.get_default_trading_account()

            if existing_default is not None and existing_default.account_id == account_id:
                return

            if existing_default is not None:
                existing_default.is_default = False
                self.m_repository.update_trading_account(existing_default)

            target.is_default = True
            self.m_repository.update_trading_account(target)

    def archive_trading_account(
        self,
        account_id: int,
    ) -> bool:
        """
        Archive a trading account without deleting its history.

        Args:
            account_id:
                Identifier of the account to archive.

        Returns:
            bool:
                True if archived, False if not found.

        Raises:
            ValueError:
                If the account is currently the default.
        """
        with self._transaction():
            account = self.m_repository.get_trading_account(account_id)

            if account is None:
                return False

            if account.is_default:
                raise ValueError("Cannot archive the default account. Select another default first.")

            if not account.is_active:
                return True

            account.is_active = False

            return self.m_repository.update_trading_account(account)

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

        with self._transaction():
            if self.m_repository.get_position(normalized.position_id) is None:
                raise ValueError("Position does not exist.")

            execution_id = self.m_repository.create_execution(normalized)

            self.validate_position_history(normalized.position_id)

            return execution_id

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

        with self._transaction():
            existing = self.m_repository.get_execution(normalized.execution_id)

            if existing is None:
                return False

            if existing.position_id != normalized.position_id:
                raise ValueError("Cannot move an execution to another position.")

            updated = self.m_repository.update_execution(normalized)

            self.validate_position_history(normalized.position_id)

            return updated

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
        with self._transaction():
            existing = self.m_repository.get_execution(execution_id)

            if existing is None:
                return False

            deleted = self.m_repository.delete_execution(execution_id)

            self.validate_position_history(existing.position_id)

            return deleted

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

        with self._transaction():
            return self.m_repository.create_account_transaction(normalized)

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

        with self._transaction():
            existing = self.m_repository.get_account_transaction(normalized.transaction_id)

            if existing is None:
                return False

            return self.m_repository.update_account_transaction(normalized)

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
        with self._transaction():
            return self.m_repository.delete_account_transaction(transaction_id)

    def create_position(
        self,
        position: Position,
    ) -> int:
        """
        Validate and create a journal position.

        Args:
            position:
                Position to create.

        Returns:
            int:
                Identifier of the created position.
        """
        validate_position(position)

        normalized = replace(
            position,
            position_id=None,
            ticker=position.ticker.strip().upper(),
        )

        with self._transaction():
            return self.m_repository.create_position(normalized)

    def update_position(
        self,
        position: Position,
    ) -> bool:
        """
        Update a position without modifying its executions.

        Args:
            position:
                Position containing updated information.

        Returns:
            bool:
                True if updated, False if not found.
        """
        if position.position_id is None:
            raise ValueError("Cannot update a position without an ID.")

        validate_position(position)

        normalized = replace(
            position,
            ticker=position.ticker.strip().upper(),
        )

        with self._transaction():
            existing = self.m_repository.get_position(normalized.position_id)

            if existing is None:
                return False

            return self.m_repository.update_position(normalized)

    def delete_position(
        self,
        position_id: int,
    ) -> bool:
        """
        Delete an empty position without losing trade history.

        Args:
            position_id:
                Identifier of the position to delete.

        Returns:
            bool:
                True if deleted, False if not found.

        Raises:
            ValueError:
                If the position contains executions.
        """
        with self._transaction():
            existing = self.m_repository.get_position(position_id)

            if existing is None:
                return False

            executions = self.m_repository.get_position_executions(position_id)

            if executions:
                raise ValueError("Cannot delete a position with executions.")

            return self.m_repository.delete_position(position_id)
