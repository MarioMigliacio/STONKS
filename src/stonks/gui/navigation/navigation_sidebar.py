# =============================================================================
# File: navigation_sidebar.py
# Purpose: Provides sidebar controls for the STONKS application.
# =============================================================================

from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class NavigationSidebar(QFrame):
    """
    Represent the persistent STONKS navigation sidebar.

    Provides controls for accessing the application's primary
    functional areas.
    """

    def __init__(self) -> None:
        """Initialize the sidebar and its navigation controls."""
        super().__init__()

        self.setFixedWidth(220)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Construct the sidebar layout and navigation buttons."""
        layout = QVBoxLayout(self)

        title = QLabel("STONKS")
        layout.addWidget(title)

        layout.addSpacing(20)

        self.m_dashboard_button = QPushButton("Dashboard")
        self.m_journal_button = QPushButton("Journal")
        self.m_accounts_button = QPushButton("Accounts")
        self.m_scanner_button = QPushButton("Scanner")
        self.m_cia_button = QPushButton("C.I.A.")

        layout.addWidget(self.m_dashboard_button)
        layout.addWidget(self.m_journal_button)
        layout.addWidget(self.m_accounts_button)
        layout.addWidget(self.m_scanner_button)
        layout.addWidget(self.m_cia_button)

        layout.addStretch()
