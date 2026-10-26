# =============================================================================
# File: main_window.py
# Purpose: Defines the main desktop application window for STONKS.
# =============================================================================

from typing import Optional

from PySide6.QtCore import Slot
from PySide6.QtGui import QCloseEvent
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
from stonks.gui.pages.scanner_page import ScannerPage
from stonks.gui.workers.scanner_thread_controller import ScannerThreadController
from stonks.journal.journal_context import JournalContext
from stonks.scanner.existing_scanner_strategy import ExistingScannerStrategy
from stonks.scanner.scanner_match_mode import ScannerMatchMode


class MainWindow(QMainWindow):
    """
    Represent the primary STONKS desktop application window.

    Coordinates the persistent navigation sidebar and central
    application pages, including the trading journal and
    account management interfaces.

    Also coordinates scanner execution outcomes and workspace status.

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

        m_scanner_controller:
            Controller that owns the active scanner thread, if any.

        m_close_pending:
            Whether a window close is waiting for scanner shutdown.

        m_scanner_page:
            Scanner workspace page presenting scan configuration.
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
        self.resize(1200, 800)

        self.m_close_pending = False
        self.m_scanner_controller = ScannerThreadController(self)
        self.m_scanner_controller.idle.connect(self._on_scanner_idle)

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
            if page_name == "scanner":
                page = ScannerPage(
                    strategies=[
                        ("existing_scanner", "Standard Market Scanner"),
                    ]
                )
                self.m_scanner_page = page

            elif page_name == "accounts" and self.m_journal_context is not None:
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
                self.m_scanner_page: Optional[ScannerPage] = None

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

        self.m_scanner_page.run_requested.connect(self._on_scanner_run_requested)
        self.m_scanner_page.cancel_requested.connect(self.m_scanner_controller.request_cancel)
        self.m_scanner_controller.running_changed.connect(self.m_scanner_page.set_running)
        self.m_scanner_controller.completed.connect(self._on_scanner_completed)
        self.m_scanner_controller.failed.connect(self._on_scanner_failed)
        self.m_scanner_controller.cancelled.connect(self._on_scanner_cancelled)

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

    @Slot(object, object)
    def _on_scanner_run_requested(
        self,
        strategy_ids: list[str],
        match_mode: ScannerMatchMode,
    ) -> None:
        """
        Start selected scanner strategies without blocking the GUI.

        Args:
            strategy_ids:
                Selected scanner strategy identifiers.

            match_mode:
                ANY or ALL matching rule.
        """
        strategy_factories = {
            "existing_scanner": lambda event: ExistingScannerStrategy(cancel_event=event),
        }
        try:
            factories = [strategy_factories[identifier] for identifier in strategy_ids]
            started = self.m_scanner_controller.start_scan(
                strategy_factories=factories,
                match_mode=match_mode,
            )
        except (KeyError, ValueError) as exc:
            self.m_scanner_page.set_status(f"Unable to start scan: {exc}")
            return

        if not started:
            self.m_scanner_page.set_status("A scan is already running.")

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Defer closing while a scanner thread is still active.

        Args:
            event: Qt window close event to accept or ignore.
        """
        if self.m_scanner_controller.is_running():
            event.ignore()
            self.m_close_pending = True
            self.m_scanner_controller.request_cancel()
            return

        self.m_close_pending = False
        super().closeEvent(event)

    @Slot()
    def _on_scanner_idle(self) -> None:
        """Retry deferred window closure after the scanner thread exits."""
        if not self.m_close_pending:
            return

        self.m_close_pending = False
        self.close()

    @Slot(list)
    def _on_scanner_completed(self, candidates: list) -> None:
        """
        Display successfully completed scan results.

        Args:
            candidates:
                ScannerCandidate objects returned by the coordinator.
        """
        self.m_scanner_page.set_results(candidates)
        count = len(candidates)
        if count == 0:
            message = "Scan complete: no matches."
        elif count == 1:
            message = "Scan complete: 1 match."
        else:
            message = f"Scan complete: {count} matches."
        self.m_scanner_page.set_status(message)

    @Slot(str)
    def _on_scanner_failed(self, message: str) -> None:
        """
        Display a scanner failure without discarding previous results.

        Args:
            message:
                Human-readable failure reported by the worker.
        """
        self.m_scanner_page.set_status(f"Scan failed: {message}")

    @Slot()
    def _on_scanner_cancelled(self) -> None:
        """Show cancellation without discarding prior successful results."""
        self.m_scanner_page.set_status("Scan cancelled.")
