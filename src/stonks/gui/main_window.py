# =============================================================================
# File: main_window.py
# Purpose: Defines the main desktop application window for STONKS.
# =============================================================================

from typing import Optional

from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from stonks.gui.navigation.navigation_sidebar import NavigationSidebar
from stonks.gui.pages.accounts_page import AccountsPage
from stonks.gui.pages.placeholder_page import PlaceholderPage
from stonks.gui.pages.positions_page import PositionsPage
from stonks.journal.journal_context import JournalContext


class MainWindow(QMainWindow):
    """
    Represent the primary STONKS desktop application window.

    Coordinates the persistent navigation sidebar and central
    application pages, including the trading journal and
    account management interfaces.

    Attributes:
        m_journal_context:
            Optional journal application context providing shared
            repository and service instances.

        m_sidebar:
            Persistent navigation sidebar used to switch pages.

        m_pages:
            Stacked widget containing application pages.

        m_page_indices:
            Mapping of page identifiers to stacked widget indices.

        m_accounts_page:
            Optional reference to the trading accounts interface.

        m_positions_page:
            Optional reference to the trading journal interface.
    """

    def __init__(
        self,
        journal_context: Optional[JournalContext] = None,
    ) -> None:
        """
        Initialize the STONKS application window.

        Args:
            journal_context:
                Optional initialized journal application context.
        """
        super().__init__()

        self.m_journal_context = journal_context

        self.setWindowTitle("STONKS - Trading Intelligence")
        self.setMinimumSize(900, 600)
        self.resize(900, 600)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Construct the application shell and navigation pages."""
        central_widget = QWidget(self)
        main_layout = QHBoxLayout(central_widget)

        # Create the persistent navigation sidebar.
        self.m_sidebar = NavigationSidebar()

        # Create the container for application pages.
        self.m_pages = QStackedWidget()
        self.m_page_indices = {}

        # Store references to functional pages for future coordination.
        self.m_accounts_page: Optional[AccountsPage] = None
        self.m_positions_page: Optional[PositionsPage] = None

        # Define our initial application pages.
        page_definitions = {
            "dashboard": "Dashboard",
            "journal": "Trading Journal",
            "accounts": "Trading Accounts",
            "scanner": "Market Scanner",
            "cia": "Catalyst Intelligence Analysis",
        }

        # Create functional pages where available; otherwise use placeholders.
        for page_name, display_name in page_definitions.items():
            if page_name == "accounts" and self.m_journal_context is not None:
                page = AccountsPage(
                    repository=self.m_journal_context.m_repository,
                    service=self.m_journal_context.m_service,
                )

                self.m_accounts_page = page

            elif page_name == "journal" and self.m_journal_context is not None:
                page = PositionsPage(
                    repository=self.m_journal_context.m_repository,
                    service=self.m_journal_context.m_service,
                )

                self.m_positions_page = page

            else:
                page = PlaceholderPage(display_name)

            page_index = self.m_pages.addWidget(page)
            self.m_page_indices[page_name] = page_index

        # Add the sidebar and page container to the main layout.
        main_layout.addWidget(self.m_sidebar)
        main_layout.addWidget(self.m_pages, stretch=1)

        # Connect sidebar navigation requests to the main window.
        self.m_sidebar.navigation_requested.connect(self._navigate_to)

        # Assign the completed layout to the window.
        self.setCentralWidget(central_widget)

    def _navigate_to(self, page_name: str) -> None:
        """
        Display the requested application page.

        Refreshes journal account selections before showing the
        journal page so changes made in account management are
        reflected without restarting the application.

        Args:
            page_name:
                Identifier of the page to display.
        """
        page_index = self.m_page_indices.get(page_name)

        if page_index is None:
            return

        # Synchronize trading accounts before opening the journal.
        if page_name == "journal" and self.m_positions_page is not None:
            self.m_positions_page.refresh_accounts()

        self.m_pages.setCurrentIndex(page_index)
