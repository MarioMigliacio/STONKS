# =============================================================================
# File: test_main_window.py
# Purpose: Verify STONKS desktop application navigation and window behavior.
# =============================================================================

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton

from stonks.gui.main_window import MainWindow


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
