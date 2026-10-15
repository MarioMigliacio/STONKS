# =============================================================================
# File: test_accounts_page.py
# Purpose: Pytest file for test_accounts_page.py.
# =============================================================================

from pathlib import Path

from PySide6.QtWidgets import QDialog

from stonks.gui.pages.accounts_page import AccountsPage
from stonks.gui.pages.create_account_dialog import CreateAccountDialog
from stonks.journal.journal_context import JournalContext
from stonks.journal.models.account_type import AccountType
from stonks.journal.models.trading_account import TradingAccount


def test_accounts_page_displays_database_records(
    qtbot,
    tmp_path: Path,
) -> None:
    """Verify the accounts page displays stored trading accounts."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        journal.m_connection.execute(
            """
            INSERT INTO trading_accounts (
                name,
                account_type,
                broker
            )
            VALUES (?, ?, ?)
            """,
            ("Retirement Account", "ROTH_IRA", "Webull"),
        )

        journal.m_connection.commit()

        page = AccountsPage(journal.m_repository)
        qtbot.addWidget(page)

        assert page.m_table.rowCount() == 1

        assert page.m_table.item(0, 0).text() == "Retirement Account"
        assert page.m_table.item(0, 1).text() == "Roth Ira"
        assert page.m_table.item(0, 2).text() == "Webull"
        assert page.m_table.item(0, 3).text() == "Active"


def test_accounts_page_handles_empty_database(
    qtbot,
    tmp_path: Path,
) -> None:
    """Verify the accounts page handles an empty journal."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        page = AccountsPage(journal.m_repository)
        qtbot.addWidget(page)

        assert page.m_table.rowCount() == 0


def test_accounts_page_displays_default_account(
    qtbot,
    tmp_path: Path,
) -> None:
    """Verify the default trading account is identified in the table."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        journal.m_service.create_trading_account(
            TradingAccount(
                name="Webull Roth IRA",
                account_type=AccountType.ROTH_IRA,
                broker="Webull",
            )
        )

        journal.m_service.create_trading_account(
            TradingAccount(
                name="Webull Cash",
                account_type=AccountType.CASH,
                broker="Webull",
            )
        )

        page = AccountsPage(journal.m_repository)
        qtbot.addWidget(page)

        assert page.m_table.columnCount() == 5
        assert page.m_table.rowCount() == 2

        assert page.m_table.item(0, 4).text() == "★ Yes"
        assert page.m_table.item(1, 4).text() == "—"


def test_accounts_page_returns_selected_account_id(
    qtbot,
    tmp_path: Path,
) -> None:
    """Verify account selection returns the database identifier."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        account_id = journal.m_service.create_trading_account(
            TradingAccount(
                name="Webull Roth IRA",
                account_type=AccountType.ROTH_IRA,
                broker="Webull",
            )
        )

        page = AccountsPage(journal.m_repository)
        qtbot.addWidget(page)

        page.m_table.selectRow(0)

        assert page.get_selected_account_id() == account_id


def test_accounts_page_preserves_selection_on_refresh(
    qtbot,
    tmp_path: Path,
) -> None:
    """Verify refreshing account data preserves the selected account."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        account_id = journal.m_service.create_trading_account(
            TradingAccount(
                name="Webull Roth IRA",
                account_type=AccountType.ROTH_IRA,
                broker="Webull",
            )
        )

        page = AccountsPage(journal.m_repository)
        qtbot.addWidget(page)

        page.m_table.selectRow(0)

        page.refresh_accounts()

        assert page.get_selected_account_id() == account_id


def test_accounts_page_edit_persists_changes(
    qtbot,
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Verify editing an account updates SQLite and refreshes the table."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        account_id = journal.m_service.create_trading_account(
            TradingAccount(
                name="Webull Cash",
                account_type=AccountType.CASH,
                broker="Webull",
            )
        )

        page = AccountsPage(
            repository=journal.m_repository,
            service=journal.m_service,
        )
        qtbot.addWidget(page)

        page.m_table.selectRow(0)

        def accept_edit(dialog):
            dialog.m_name.setText("Updated Cash Account")
            dialog.m_broker.setText("Updated Broker")
            return QDialog.Accepted

        monkeypatch.setattr(
            CreateAccountDialog,
            "exec",
            accept_edit,
        )

        page.m_edit_action.trigger()

        stored_account = journal.m_repository.get_trading_account(account_id)

        assert stored_account is not None
        assert stored_account.name == "Updated Cash Account"
        assert stored_account.broker == "Updated Broker"
        assert stored_account.is_default is True

        assert page.m_table.item(0, 0).text() == "Updated Cash Account"
        assert page.get_selected_account_id() == account_id


def test_accounts_page_edit_cancelled(
    qtbot,
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Verify canceling an edit leaves the trading account unchanged."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        account_id = journal.m_service.create_trading_account(
            TradingAccount(
                name="Webull Cash",
                account_type=AccountType.CASH,
                broker="Webull",
            )
        )

        page = AccountsPage(
            repository=journal.m_repository,
            service=journal.m_service,
        )
        qtbot.addWidget(page)

        page.m_table.selectRow(0)

        monkeypatch.setattr(
            CreateAccountDialog,
            "exec",
            lambda dialog: QDialog.Rejected,
        )

        page.m_edit_action.trigger()

        stored_account = journal.m_repository.get_trading_account(account_id)

        assert stored_account is not None
        assert stored_account.name == "Webull Cash"
        assert stored_account.broker == "Webull"


def test_accounts_page_switches_default_account(
    qtbot,
    tmp_path: Path,
) -> None:
    """Verify the selected account becomes the new default."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        roth_id = journal.m_service.create_trading_account(
            TradingAccount(
                name="Webull Roth IRA",
                account_type=AccountType.ROTH_IRA,
                broker="Webull",
            )
        )

        cash_id = journal.m_service.create_trading_account(
            TradingAccount(
                name="Webull Cash",
                account_type=AccountType.CASH,
                broker="Webull",
            )
        )

        page = AccountsPage(
            repository=journal.m_repository,
            service=journal.m_service,
        )
        qtbot.addWidget(page)

        # Select the second account.
        page.m_table.selectRow(1)

        assert page.m_default_action.isEnabled()

        # Trigger the same QAction used by the menu.
        page.m_default_action.trigger()

        roth = journal.m_repository.get_trading_account(roth_id)
        cash = journal.m_repository.get_trading_account(cash_id)

        assert roth.is_default is False
        assert cash.is_default is True

        # Verify the visible table reflects the change.
        assert page.m_table.item(0, 4).text() == "—"
        assert page.m_table.item(1, 4).text() == "★ Yes"

        # Account selection should remain unchanged.
        assert page.get_selected_account_id() == cash_id

        # The new default can no longer trigger the action.
        assert not page.m_default_action.isEnabled()


def test_default_action_disabled_for_current_default(
    qtbot,
    tmp_path: Path,
) -> None:
    """Verify an existing default account cannot be selected again."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        journal.m_service.create_trading_account(
            TradingAccount(
                name="Webull Roth IRA",
                account_type=AccountType.ROTH_IRA,
                broker="Webull",
            )
        )

        page = AccountsPage(
            repository=journal.m_repository,
            service=journal.m_service,
        )
        qtbot.addWidget(page)

        page.m_table.selectRow(0)

        assert page.m_actions_button.isEnabled()
        assert not page.m_default_action.isEnabled()


def test_default_switch_persists_after_reopening(
    qtbot,
    tmp_path: Path,
) -> None:
    """Verify default account changes persist across database sessions."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        journal.m_service.create_trading_account(
            TradingAccount(
                name="Webull Roth IRA",
                account_type=AccountType.ROTH_IRA,
            )
        )

        cash_id = journal.m_service.create_trading_account(
            TradingAccount(
                name="Webull Cash",
                account_type=AccountType.CASH,
            )
        )

        page = AccountsPage(
            repository=journal.m_repository,
            service=journal.m_service,
        )
        qtbot.addWidget(page)

        page.m_table.selectRow(1)
        page.m_default_action.trigger()

    # Reopen the database in a new application context.
    with JournalContext(database_path) as reopened:
        default_account = reopened.m_repository.get_default_trading_account()

        assert default_account is not None
        assert default_account.account_id == cash_id
