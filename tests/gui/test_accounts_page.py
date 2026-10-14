# =============================================================================
# File: test_accounts_page.py
# Purpose: Pytest file for test_accounts_page.py.
# =============================================================================

from pathlib import Path

from stonks.gui.pages.accounts_page import AccountsPage
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

        assert page.get_selected_account_id() is None

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