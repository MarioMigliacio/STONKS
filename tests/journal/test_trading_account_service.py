# =============================================================================
# File: test_trading_account_service.py
# Purpose: Pytest file for test_trading_account_service.py.
# =============================================================================

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from stonks.journal.models.account_transaction import AccountTransaction
from stonks.journal.models.account_transaction_type import AccountTransactionType
from stonks.journal.models.account_type import AccountType
from stonks.journal.models.execution_side import ExecutionSide
from stonks.journal.models.position import Position
from stonks.journal.models.trade_execution import TradeExecution
from stonks.journal.models.trading_account import TradingAccount
from stonks.journal.persistence.journal_database import (
    create_connection,
    initialize_database,
)
from stonks.journal.services.journal_service import JournalService


@pytest.fixture
def service(tmp_path):
    """Create an isolated service with the complete journal schema."""
    database_path = tmp_path / "accounts.db"

    initialize_database(database_path)
    connection = create_connection(database_path)

    yield JournalService(connection)

    connection.close()


def test_first_account_becomes_default(service) -> None:
    """Verify the first account is automatically selected."""
    account_id = service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))

    account = service.m_repository.get_trading_account(account_id)

    assert account is not None
    assert account.is_default is True


def test_create_second_account(service) -> None:
    """Verify subsequent accounts are not default automatically."""
    service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))

    account_id = service.create_trading_account(TradingAccount("Cash Account", AccountType.CASH))

    account = service.m_repository.get_trading_account(account_id)

    assert account is not None
    assert account.is_default is False


def test_switch_default_account(service) -> None:
    """Verify switching defaults updates both accounts atomically."""
    first_id = service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))
    second_id = service.create_trading_account(TradingAccount("Cash Account", AccountType.CASH))

    service.set_default_trading_account(second_id)

    first = service.m_repository.get_trading_account(first_id)
    second = service.m_repository.get_trading_account(second_id)

    assert first.is_default is False
    assert second.is_default is True


def test_reject_archived_default(service) -> None:
    """Verify an archived account cannot become the default."""
    service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))

    archived_id = service.create_trading_account(
        TradingAccount(
            "Old Cash",
            AccountType.CASH,
            is_active=False,
        )
    )

    with pytest.raises(ValueError):
        service.set_default_trading_account(archived_id)


def test_archive_account(service) -> None:
    """Verify archiving preserves the account record."""
    service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))

    account_id = service.create_trading_account(TradingAccount("Old Cash", AccountType.CASH))

    assert service.archive_trading_account(account_id) is True

    account = service.m_repository.get_trading_account(account_id)

    assert account is not None
    assert account.is_active is False
    assert account.is_default is False


def test_reactivate_trading_account(service) -> None:
    """
    Verify an archived account can be reactivated.

    Reactivation must preserve the account's identity and
    must not modify the existing default account.
    """
    default_id = service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))

    account_id = service.create_trading_account(TradingAccount("Old Cash", AccountType.CASH))

    # Archive the non-default account.
    assert service.archive_trading_account(account_id) is True

    archived = service.m_repository.get_trading_account(account_id)

    assert archived is not None
    assert archived.is_active is False

    # Reactivate the account.
    assert service.reactivate_trading_account(account_id) is True

    reactivated = service.m_repository.get_trading_account(account_id)

    assert reactivated is not None
    assert reactivated.account_id == account_id
    assert reactivated.is_active is True
    assert reactivated.is_default is False

    # Verify the original default account remains unchanged.
    default_account = service.m_repository.get_default_trading_account()

    assert default_account is not None
    assert default_account.account_id == default_id

    # Reactivation is idempotent.
    assert service.reactivate_trading_account(account_id) is True

    # Nonexistent accounts return False.
    assert service.reactivate_trading_account(999999) is False


def test_cannot_archive_default(service) -> None:
    """Verify default accounts require reassignment before archival."""
    account_id = service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))

    with pytest.raises(ValueError):
        service.archive_trading_account(account_id)

    account = service.m_repository.get_trading_account(account_id)

    assert account is not None
    assert account.is_active is True
    assert account.is_default is True


def test_update_account_details(service) -> None:
    """Verify account metadata can be edited."""
    account_id = service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))

    account = service.m_repository.get_trading_account(account_id)
    account.name = "Retirement IRA"
    account.broker = "Webull"

    assert service.update_trading_account(account) is True

    updated = service.m_repository.get_trading_account(account_id)

    assert updated.name == "Retirement IRA"
    assert updated.broker == "Webull"


def test_reject_default_change_through_update(service) -> None:
    """Verify default selection uses its dedicated service method."""
    account_id = service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))

    account = service.m_repository.get_trading_account(account_id)
    account.is_default = False

    with pytest.raises(ValueError):
        service.update_trading_account(account)

    persisted = service.m_repository.get_trading_account(account_id)

    assert persisted.is_default is True


def test_default_switch_rolls_back_on_failure(
    service,
    monkeypatch,
) -> None:
    """Verify a failed default switch preserves the original default."""
    first_id = service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))
    second_id = service.create_trading_account(TradingAccount("Cash Account", AccountType.CASH))

    original_update = service.m_repository.update_trading_account

    def fail_on_new_default(account):
        """Simulate failure while assigning the new default."""
        if account.account_id == second_id:
            raise RuntimeError("Simulated database failure.")

        return original_update(account)

    monkeypatch.setattr(
        service.m_repository,
        "update_trading_account",
        fail_on_new_default,
    )

    with pytest.raises(RuntimeError, match="Simulated database failure"):
        service.set_default_trading_account(second_id)

    original = service.m_repository.get_trading_account(first_id)
    target = service.m_repository.get_trading_account(second_id)

    assert original.is_default is True
    assert target.is_default is False


def test_cannot_create_archived_first_account(service) -> None:
    """Verify the first trading account must be active."""
    with pytest.raises(ValueError):
        service.create_trading_account(
            TradingAccount(
                "Archived Account",
                AccountType.CASH,
                is_active=False,
            )
        )

    assert service.m_repository.get_trading_accounts() == []


def test_account_ownership_rejects_missing_account(service) -> None:
    """Reject activity assigned to a nonexistent trading account."""
    with pytest.raises(
        ValueError,
        match="does not exist",
    ):
        service._validate_account_ownership(999)


def test_account_ownership_accepts_active_account(service) -> None:
    """Allow activity assigned to an active trading account."""
    account_id = service.create_trading_account(
        TradingAccount(
            name="Roth IRA",
            account_type=AccountType.ROTH_IRA,
        )
    )

    service._validate_account_ownership(account_id)


def test_account_ownership_rejects_archived_account(service) -> None:
    """Reject new activity assigned to an archived trading account."""
    roth_id = service.create_trading_account(
        TradingAccount(
            name="Roth IRA",
            account_type=AccountType.ROTH_IRA,
        )
    )

    cash_id = service.create_trading_account(
        TradingAccount(
            name="Cash Account",
            account_type=AccountType.CASH,
        )
    )

    # The first account is automatically the default.
    # Switch the default before archiving it.
    service.set_default_trading_account(cash_id)

    assert service.archive_trading_account(roth_id) is True

    with pytest.raises(
        ValueError,
        match="archived",
    ):
        service._validate_account_ownership(roth_id)


def test_archived_account_rejects_new_position(
    service,
) -> None:
    """Verify archived accounts cannot receive new positions."""
    service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))

    archived_id = service.create_trading_account(TradingAccount("Old Cash", AccountType.CASH))

    assert service.archive_trading_account(archived_id) is True

    positions_before = service.m_repository.get_positions()

    with pytest.raises(ValueError, match="archived"):
        service.create_position(
            Position(
                ticker="NVDA",
                account_id=archived_id,
            )
        )

    assert service.m_repository.get_positions() == positions_before


def test_archived_account_rejects_new_transaction(
    service,
) -> None:
    """Verify archived accounts cannot receive new transactions."""
    service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))

    archived_id = service.create_trading_account(TradingAccount("Old Cash", AccountType.CASH))

    assert service.archive_trading_account(archived_id) is True

    transactions_before = service.m_repository.get_account_transactions()

    with pytest.raises(ValueError, match="archived"):
        service.create_account_transaction(
            AccountTransaction(
                transaction_type=AccountTransactionType.DEPOSIT,
                occurred_at=datetime(2026, 10, 10, 14, 30, tzinfo=timezone.utc),
                amount=Decimal("100"),
                account_id=archived_id,
            )
        )

    assert service.m_repository.get_account_transactions() == transactions_before


def test_cannot_delete_active_account(service) -> None:
    """Verify active trading accounts cannot be deleted."""
    service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))

    account_id = service.create_trading_account(TradingAccount("Active Cash", AccountType.CASH))

    with pytest.raises(ValueError, match="Archive"):
        service.delete_trading_account(account_id)

    assert service.m_repository.get_trading_account(account_id) is not None


def test_cannot_delete_default_account(service) -> None:
    """Verify the default trading account is protected."""
    account_id = service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))

    with pytest.raises(ValueError, match="default"):
        service.delete_trading_account(account_id)

    assert service.m_repository.get_trading_account(account_id) is not None


def test_delete_missing_account(service) -> None:
    """Verify deletion returns False for nonexistent accounts."""
    assert service.delete_trading_account(999999) is False


def test_delete_archived_trading_account(service) -> None:
    """Verify an archived account can be permanently deleted."""
    default_id = service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))

    archived_id = service.create_trading_account(TradingAccount("Old Cash", AccountType.CASH))

    assert service.archive_trading_account(archived_id)

    assert service.delete_trading_account(archived_id)

    assert service.m_repository.get_trading_account(archived_id) is None

    # The other account remains unaffected.
    default_account = service.m_repository.get_trading_account(default_id)

    assert default_account is not None
    assert default_account.is_default is True


def test_delete_populated_account_preserves_other_accounts(service) -> None:
    """
    Verify permanent deletion removes all owned financial records.

    Other trading accounts and their records must remain intact.
    """
    repository = service.m_repository
    timestamp = datetime(2026, 10, 15, 14, 30, tzinfo=timezone.utc)

    # Create two independent accounts.
    primary_id = service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))
    target_id = service.create_trading_account(TradingAccount("Old Cash", AccountType.CASH))

    # Give each account its own position.
    primary_position_id = service.create_position(Position(ticker="AAPL", account_id=primary_id))
    target_position_id = service.create_position(Position(ticker="NVDA", account_id=target_id))

    # Add executions to both positions.
    primary_execution_id = service.create_execution(
        TradeExecution(
            position_id=primary_position_id,
            side=ExecutionSide.BUY,
            executed_at=timestamp,
            shares=Decimal("5"),
            price=Decimal("200"),
        )
    )
    target_execution_id = service.create_execution(
        TradeExecution(
            position_id=target_position_id,
            side=ExecutionSide.BUY,
            executed_at=timestamp,
            shares=Decimal("10"),
            price=Decimal("150"),
        )
    )

    # Give each account a cash transaction.
    primary_transaction_id = service.create_account_transaction(
        AccountTransaction(
            transaction_type=AccountTransactionType.DEPOSIT,
            occurred_at=timestamp,
            amount=Decimal("1000"),
            account_id=primary_id,
        )
    )
    target_transaction_id = service.create_account_transaction(
        AccountTransaction(
            transaction_type=AccountTransactionType.DEPOSIT,
            occurred_at=timestamp,
            amount=Decimal("2000"),
            account_id=target_id,
        )
    )

    # Archive the target before deleting it.
    assert service.archive_trading_account(target_id) is True
    assert service.delete_trading_account(target_id) is True

    # Deleted account and all owned records are gone.
    assert repository.get_trading_account(target_id) is None
    assert repository.get_position(target_position_id) is None
    assert repository.get_execution(target_execution_id) is None
    assert repository.get_account_transaction(target_transaction_id) is None

    # The unrelated account and its records survive.
    assert repository.get_trading_account(primary_id) is not None
    assert repository.get_position(primary_position_id) is not None
    assert repository.get_execution(primary_execution_id) is not None
    assert repository.get_account_transaction(primary_transaction_id) is not None


def test_delete_account_rolls_back_on_failure(
    service,
    monkeypatch,
) -> None:
    """
    Verify a failed account deletion restores all financial records.

    A failure during position deletion must roll back earlier
    transaction deletions and preserve the account itself.
    """
    repository = service.m_repository
    timestamp = datetime(2026, 10, 15, 14, 30, tzinfo=timezone.utc)

    service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))

    target_id = service.create_trading_account(TradingAccount("Old Cash", AccountType.CASH))

    position_id = service.create_position(Position(ticker="NVDA", account_id=target_id))

    execution_id = service.create_execution(
        TradeExecution(
            position_id=position_id,
            side=ExecutionSide.BUY,
            executed_at=timestamp,
            shares=Decimal("10"),
            price=Decimal("150"),
        )
    )

    transaction_id = service.create_account_transaction(
        AccountTransaction(
            transaction_type=AccountTransactionType.DEPOSIT,
            occurred_at=timestamp,
            amount=Decimal("2000"),
            account_id=target_id,
        )
    )

    assert service.archive_trading_account(target_id) is True

    # Add a temporary trigger to simulate a database failure
    # when the repository attempts to delete positions.
    service.m_connection.execute(
        """
        CREATE TEMP TRIGGER block_position_deletion
        BEFORE DELETE ON main.positions
        BEGIN
            SELECT RAISE(ABORT, 'Simulated deletion failure');
        END
        """
    )

    # Ensure trigger setup does not leave an active transaction.
    service.m_connection.commit()

    try:
        with pytest.raises(
            Exception,
            match="Simulated deletion failure",
        ):
            service.delete_trading_account(target_id)

    finally:
        service.m_connection.execute("DROP TRIGGER IF EXISTS temp.block_position_deletion")
        service.m_connection.commit()

    # Nothing should have been permanently deleted.
    account = repository.get_trading_account(target_id)

    assert account is not None
    assert account.is_active is False

    assert repository.get_position(position_id) is not None
    assert repository.get_execution(execution_id) is not None
    assert repository.get_account_transaction(transaction_id) is not None

    # The service transaction should be fully rolled back.
    assert service.m_connection.in_transaction is False


def test_account_deletion_requires_foreign_keys(service) -> None:
    """Verify foreign-key protection is enabled for deletion operations."""
    enabled = service.m_connection.execute("PRAGMA foreign_keys").fetchone()[0]

    assert enabled == 1
