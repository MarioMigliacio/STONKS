# =============================================================================
# File: journal_service.py
# Purpose: Enforce journal business rules and transaction integrity.
# =============================================================================

import sqlite3
from contextlib import contextmanager
from dataclasses import replace
from decimal import Decimal
from typing import Generator, Optional

from stonks.journal.models.account_transaction import AccountTransaction
from stonks.journal.models.account_transaction_type import AccountTransactionType
from stonks.journal.models.execution_side import ExecutionSide
from stonks.journal.models.position import Position
from stonks.journal.models.trade_execution import TradeExecution
from stonks.journal.models.trading_account import TradingAccount
from stonks.journal.persistence.journal_repository import JournalRepository
from stonks.journal.validation.account_validation import validate_trading_account
from stonks.journal.validation.journal_validation import (
    normalize_timestamp,
    validate_account_transaction,
    validate_execution,
    validate_position,
)


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

    def delete_trading_account(
        self,
        account_id: int,
    ) -> bool:
        """
        Permanently delete an archived trading account.

        Removes the account, its positions, trade executions,
        and financial transactions in a single transaction.

        Active and default trading accounts cannot be deleted.

        Args:
            account_id:
                Identifier of the trading account to delete.

        Returns:
            bool:
                True if the account was deleted, False if it
                does not exist.

        Raises:
            ValueError:
                If the account is active or currently the default.

            RuntimeError:
                If a transaction is already active.
        """
        with self._transaction():
            account = self.m_repository.get_trading_account(account_id)

            if account is None:
                return False

            if account.is_default:
                raise ValueError("Cannot delete the default account. Select another default account first.")

            if account.is_active:
                raise ValueError("Cannot delete an active account. Archive the account before deleting it.")

            return self.m_repository.delete_trading_account(account_id)

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

    def reactivate_trading_account(
        self,
        account_id: int,
    ) -> bool:
        """
        Reactivate an archived trading account.

        Restores the account to active status without modifying its
        default designation or historical financial records.

        Args:
            account_id:
                Identifier of the trading account to reactivate.

        Returns:
            bool:
                True if the account is active after the operation,
                False if the account does not exist.
        """
        with self._transaction():
            account = self.m_repository.get_trading_account(account_id)

            if account is None:
                return False

            if account.is_active:
                return True

            account.is_active = True

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
            position = self.m_repository.get_position(normalized.position_id)

            if position is None:
                raise ValueError("Position does not exist.")

            self._validate_account_ownership(position.account_id)

            execution_id = self.m_repository.create_execution(normalized)

            self.validate_position_history(normalized.position_id)

            return execution_id

    def update_execution(
        self,
        execution: TradeExecution,
    ) -> bool:
        """
        Update an execution while preserving position integrity.

        Revalidates the complete execution history after modification,
        prevents moving executions between positions, and prohibits
        modifications to archived trading accounts.

        Args:
            execution:
                Execution containing the updated values.

        Returns:
            bool:
                True if updated, False if the execution does not exist.

        Raises:
            ValueError:
                If the update violates execution validation, account
                ownership, or chronological position integrity.
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

            # The GUI is not the only potential caller. Protect
            # archived accounts at the service layer as well.
            position = self.m_repository.get_position(existing.position_id)

            if position is None:
                raise ValueError("Position does not exist.")

            self._validate_account_ownership(position.account_id)

            updated = self.m_repository.update_execution(normalized)

            # Invalid history raises ValueError and rolls back
            # the entire transaction automatically.
            self.validate_position_history(normalized.position_id)

            return updated

    def delete_execution(
        self,
        execution_id: int,
    ) -> bool:
        """
        Delete an execution if the remaining position history stays valid.

        Prohibits deletion from archived trading accounts and
        atomically rolls back changes that would invalidate
        the position's chronological execution history.

        Args:
            execution_id:
                Identifier of the execution to remove.

        Returns:
            bool:
                True if deleted, False if the execution does not exist.

        Raises:
            ValueError:
                If the execution belongs to an archived account
                or deleting it invalidates the remaining history.
        """
        with self._transaction():
            existing = self.m_repository.get_execution(execution_id)

            if existing is None:
                return False

            position = self.m_repository.get_position(existing.position_id)

            if position is None:
                raise ValueError("Position does not exist.")

            # Protect archived accounts regardless of which
            # interface requests the deletion.
            self._validate_account_ownership(position.account_id)

            deleted = self.m_repository.delete_execution(execution_id)

            # If this raises ValueError, the transaction manager
            # restores the execution and leaves history unchanged.
            self.validate_position_history(existing.position_id)

            return deleted

    def create_account_transfer(
        self,
        source_account_id: int,
        destination_account_id: int,
        amount: Decimal,
        occurred_at,
        notes: str = "",
    ) -> tuple:
        """Create a linked internal transfer and both ledger legs atomically.

        Args:
            source_account_id:
                Trading account sending cash.
            destination_account_id:
                Trading account receiving cash.
            amount:
                Positive, finite Decimal amount to transfer.
            occurred_at:
                Timezone-aware timestamp for both ledger movements.
            notes:
                Optional text describing the transfer.

        Returns:
            tuple:
                Outgoing and incoming transaction identifiers.

        Raises:
            ValueError:
                If accounts, amount, or timestamp are invalid.
        """
        if source_account_id == destination_account_id:
            raise ValueError("Source and destination accounts must differ.")
        if not isinstance(amount, Decimal) or not amount.is_finite() or amount <= 0:
            raise ValueError("Transfer amount must be a positive finite Decimal.")
        timestamp = normalize_timestamp(occurred_at)

        with self._transaction():
            self._validate_account_ownership(source_account_id)
            self._validate_account_ownership(destination_account_id)

            cursor = self.m_connection.execute(
                """
                INSERT INTO account_transfers (
                    source_account_id, destination_account_id, amount,
                    occurred_at, notes
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    source_account_id,
                    destination_account_id,
                    str(amount),
                    timestamp.isoformat(),
                    notes,
                ),
            )
            transfer_id = cursor.lastrowid
            if transfer_id is None:
                raise RuntimeError("Failed to create account transfer.")

            outgoing = AccountTransaction(
                account_id=source_account_id,
                transaction_type=AccountTransactionType.TRANSFER_OUT,
                amount=amount,
                occurred_at=timestamp,
                notes=notes,
                transfer_id=transfer_id,
            )
            incoming = AccountTransaction(
                account_id=destination_account_id,
                transaction_type=AccountTransactionType.TRANSFER_IN,
                amount=amount,
                occurred_at=timestamp,
                notes=notes,
                transfer_id=transfer_id,
            )
            outgoing_id = self.m_repository.create_account_transaction(outgoing)
            incoming_id = self.m_repository.create_account_transaction(incoming)
            return outgoing_id, incoming_id

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
        if (
            transaction.transaction_type
            in (
                AccountTransactionType.TRANSFER_IN,
                AccountTransactionType.TRANSFER_OUT,
            )
            or transaction.transfer_id is not None
        ):
            raise ValueError("Transfers must use create_account_transfer().")

        validate_account_transaction(transaction)

        normalized = AccountTransaction(
            transaction_type=transaction.transaction_type,
            occurred_at=normalize_timestamp(transaction.occurred_at),
            amount=transaction.amount,
            transaction_id=None,
            account_id=transaction.account_id,
            notes=transaction.notes,
        )

        with self._transaction():
            self._validate_account_ownership(normalized.account_id)
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
            account_id=transaction.account_id,
            notes=transaction.notes,
        )

        with self._transaction():
            existing = self.m_repository.get_account_transaction(normalized.transaction_id)

            if existing is None:
                return False

            if existing.transfer_id is not None or normalized.transaction_type in (
                AccountTransactionType.TRANSFER_IN,
                AccountTransactionType.TRANSFER_OUT,
            ):
                raise ValueError("Cannot edit a transfer leg independently.")

            if existing.account_id != normalized.account_id:
                raise ValueError("Cannot move a transaction to another trading account.")

            self._validate_account_ownership(existing.account_id)
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
            existing = self.m_repository.get_account_transaction(transaction_id)
            if existing is not None and existing.transfer_id is not None:
                raise ValueError("Cannot delete a transfer leg independently.")
            existing = self.m_repository.get_account_transaction(transaction_id)
            if existing is None:
                return False
            self._validate_account_ownership(existing.account_id)
            return self.m_repository.delete_account_transaction(transaction_id)

    def _validate_account_ownership(
        self,
        account_id: Optional[int],
    ) -> None:
        """
        Validate that an account exists and accepts new activity.

        Args:
            account_id:
                Identifier of the trading account to validate.

        Raises:
            ValueError:
                If the account ID is missing, the account does not
                exist, or the account is archived.
        """
        if account_id is None:
            raise ValueError("A trading account is required.")

        account = self.m_repository.get_trading_account(account_id)

        if account is None:
            raise ValueError(f"Trading account {account_id} does not exist.")

        if not account.is_active:
            raise ValueError(f"Trading account {account_id} is archived.")

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
            self._validate_account_ownership(normalized.account_id)
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

            if existing.account_id != normalized.account_id:
                raise ValueError("Cannot move a position to another trading account.")

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
