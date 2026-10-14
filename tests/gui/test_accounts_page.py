# =============================================================================
# File: test_accounts_page.py
# Purpose: Pytest file for test_accounts_page.py.
# =============================================================================

from pathlib import Path

from stonks.gui.pages.accounts_page import AccountsPage
from stonks.journal.journal_context import JournalContext


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
