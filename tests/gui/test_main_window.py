# =============================================================================
# File: test_main_window.py
# Purpose: Pytest file for test_main_window.py.
# =============================================================================

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton

from stonks.gui.main_window import MainWindow
from stonks.journal.journal_context import JournalContext
from stonks.journal.models.account_type import AccountType
from stonks.journal.models.trading_account import TradingAccount


@pytest.fixture
def main_window(qtbot):
    """
    Create a managed STONKS main window for GUI testing.

    Args:
        qtbot:
            Pytest-qt fixture managing Qt widgets.

    Returns:
        MainWindow:
            Initialized application window.
    """
    window = MainWindow()

    qtbot.addWidget(window)
    window.show()

    return window


def test_main_window_initializes(main_window):
    """Verify the application window initializes correctly."""
    assert main_window.windowTitle() == "STONKS - Trading Intelligence"

    assert main_window.m_sidebar is not None
    assert main_window.m_pages is not None

    assert main_window.m_pages.count() == 5


def test_dashboard_selected_by_default(main_window):
    """Verify Dashboard is selected when the application starts."""
    current_index = main_window.m_pages.currentIndex()

    assert current_index == main_window.m_page_indices["dashboard"]

    selected_button = main_window.m_sidebar.m_button_group.checkedButton()

    assert selected_button is not None
    assert selected_button.text() == "Dashboard"


def test_journal_navigation(main_window, qtbot):
    """Verify clicking Journal displays the journal page."""
    buttons = main_window.m_sidebar.findChildren(QPushButton)

    journal_button = next(button for button in buttons if button.text() == "Journal")

    qtbot.mouseClick(journal_button, Qt.LeftButton)

    assert main_window.m_pages.currentIndex() == main_window.m_page_indices["journal"]

    assert journal_button.isChecked()


def test_accounts_navigation(main_window, qtbot):
    """Verify clicking Accounts displays the accounts page."""
    buttons = main_window.m_sidebar.findChildren(QPushButton)

    accounts_button = next(button for button in buttons if button.text() == "Accounts")

    qtbot.mouseClick(accounts_button, Qt.LeftButton)

    assert main_window.m_pages.currentIndex() == main_window.m_page_indices["accounts"]

    assert accounts_button.isChecked()


def test_navigation_preserves_sidebar(main_window, qtbot):
    """Verify changing pages does not replace the sidebar."""
    original_sidebar = main_window.m_sidebar

    buttons = main_window.m_sidebar.findChildren(QPushButton)

    for button in buttons:
        qtbot.mouseClick(button, Qt.LeftButton)

        assert main_window.m_sidebar is original_sidebar

        current_page = main_window.m_pages.currentWidget()

        assert current_page is not None
        assert current_page.findChild(QLabel) is not None


def test_main_window_closes(main_window):
    """Verify the application window closes successfully."""
    main_window.close()

    assert not main_window.isVisible()


def test_main_window_refreshes_journal_accounts_on_navigation(
    qtbot,
    tmp_path,
) -> None:
    """
    Verify opening the Journal refreshes available trading accounts.

    Account changes made after window initialization must be
    visible without restarting the application.
    """
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        window = MainWindow(journal_context=journal)
        qtbot.addWidget(window)

        positions_page = window.m_positions_page

        assert positions_page is not None
        assert positions_page.m_account_selector.count() == 0

        # Simulate a new account created elsewhere in the application.
        account_id = journal.m_service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))

        # Navigate to the Journal through MainWindow.
        window._navigate_to("journal")

        assert positions_page.m_account_selector.count() == 1
        assert positions_page.get_selected_account_id() == account_id

        # Confirm that the intended page is displayed.
        assert window.m_pages.currentWidget() is positions_page
