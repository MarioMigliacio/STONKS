# =============================================================================
# File: test_trading_account_repository.py
# Purpose: Pytest file for test_trading_account_repository.py
# =============================================================================

import sqlite3

import pytest

from stonks.journal.account_type import AccountType
from stonks.journal.journal_database import (
    create_connection,
    create_trading_accounts_table,
)
from stonks.journal.journal_repository import JournalRepository
from stonks.journal.trading_account import TradingAccount


@pytest.fixture
def repository(tmp_path):
    """Create an isolated repository with an account table."""
    connection = create_connection(tmp_path / "accounts.db")

    with connection:
        create_trading_accounts_table(connection)

    yield JournalRepository(connection)

    connection.close()


def test_create_and_get_trading_account(repository) -> None:
    """Verify a trading account can be persisted and retrieved."""
    with repository.m_connection:
        account_id = repository.create_trading_account(
            TradingAccount(
                name="Primary IRA",
                account_type=AccountType.ROTH_IRA,
                broker="Webull",
                is_default=True,
            )
        )

    account = repository.get_trading_account(account_id)

    assert account is not None
    assert account.account_id == account_id
    assert account.name == "Primary IRA"
    assert account.account_type == AccountType.ROTH_IRA
    assert account.broker == "Webull"
    assert account.is_active is True
    assert account.is_default is True


def test_get_trading_accounts(repository) -> None:
    """Verify account retrieval includes active and archived accounts."""
    with repository.m_connection:
        repository.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))
        repository.create_trading_account(
            TradingAccount(
                "Archived Cash",
                AccountType.CASH,
                is_active=False,
            )
        )

    accounts = repository.get_trading_accounts()

    assert len(accounts) == 2
    assert accounts[0].name == "Primary IRA"
    assert accounts[1].name == "Archived Cash"
    assert accounts[1].is_active is False


def test_multiple_defaults_rejected(repository) -> None:
    """Verify the database rejects multiple default accounts."""
    with repository.m_connection:
        repository.create_trading_account(
            TradingAccount(
                "Primary IRA",
                AccountType.ROTH_IRA,
                is_default=True,
            )
        )

    with pytest.raises(sqlite3.IntegrityError):
        with repository.m_connection:
            repository.create_trading_account(
                TradingAccount(
                    "Secondary Cash",
                    AccountType.CASH,
                    is_default=True,
                )
            )


def test_archive_trading_account(repository) -> None:
    """Verify an account can be archived without being deleted."""
    with repository.m_connection:
        account_id = repository.create_trading_account(TradingAccount("Old Cash", AccountType.CASH))

        account = repository.get_trading_account(account_id)
        account.is_active = False

        assert repository.update_trading_account(account) is True

    archived = repository.get_trading_account(account_id)

    assert archived is not None
    assert archived.is_active is False


def test_get_default_trading_account(repository) -> None:
    """Verify the preferred trading account can be retrieved."""
    with repository.m_connection:
        repository.create_trading_account(
            TradingAccount(
                "Primary IRA",
                AccountType.ROTH_IRA,
                is_default=True,
            )
        )

    account = repository.get_default_trading_account()

    assert account is not None
    assert account.name == "Primary IRA"
