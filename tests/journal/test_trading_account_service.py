# =============================================================================
# File: test_trading_account_service.py
# Purpose: Pytest file for test_trading_account_service.py.
# =============================================================================

import pytest

from stonks.journal.account_type import AccountType
from stonks.journal.journal_database import (
    create_connection,
    create_trading_accounts_table,
)
from stonks.journal.journal_service import JournalService
from stonks.journal.trading_account import TradingAccount


@pytest.fixture
def service(tmp_path):
    """Create an isolated service with trading account persistence."""
    connection = create_connection(tmp_path / "accounts.db")

    with connection:
        create_trading_accounts_table(connection)

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
