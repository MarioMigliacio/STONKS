# =============================================================================
# File: accounts_page.py
# Purpose: Display and manage trading accounts in the STONKS GUI.
# =============================================================================

from typing import Optional

from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from stonks.gui.pages.create_account_dialog import CreateAccountDialog
from stonks.journal.persistence.journal_repository import JournalRepository
from stonks.journal.services.journal_service import JournalService


class AccountsPage(QWidget):
    """
    Display trading accounts and provide account creation controls.

    Attributes:
        m_repository:
            Repository providing trading account records.
        m_service:
            Optional service providing validated account operations.
        m_table:
            Read-only table displaying trading accounts.
        m_empty_label:
            Message displayed when no trading accounts exist.
    """

    def __init__(
        self,
        repository: JournalRepository,
        service: Optional[JournalService] = None,
    ) -> None:
        """
        Initialize the trading accounts page.

        Args:
            repository:
                Repository providing trading account data.
            service:
                Optional service used to create accounts.
        """
        super().__init__()

        self.m_repository = repository
        self.m_service = service

        self._setup_ui()
        self.refresh_accounts()

    def _setup_ui(self) -> None:
        """Construct the trading account management interface."""
        layout = QVBoxLayout(self)

        header_layout = QHBoxLayout()

        title = QLabel("Trading Accounts")
        title.setObjectName("pageTitle")

        self.m_create_button = QPushButton("New Account")
        self.m_create_button.setEnabled(self.m_service is not None)
        self.m_create_button.clicked.connect(self._create_account)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.m_create_button)

        layout.addLayout(header_layout)

        self.m_table = QTableWidget()
        self.m_table.setColumnCount(4)

        self.m_table.setHorizontalHeaderLabels(["Name", "Type", "Broker", "Status"])

        self.m_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.m_table.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.m_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.m_empty_label = QLabel("No trading accounts yet. Create your first account to begin.")
        self.m_empty_label.setObjectName("emptyState")

        layout.addWidget(self.m_table)
        layout.addWidget(self.m_empty_label)

    def refresh_accounts(self) -> None:
        """Retrieve trading accounts and refresh the display."""
        accounts = self.m_repository.get_trading_accounts()

        self.m_table.setRowCount(len(accounts))
        self.m_empty_label.setVisible(len(accounts) == 0)

        for row_index, account in enumerate(accounts):
            values = [
                account.name,
                account.account_type.value.replace("_", " ").title(),
                account.broker,
                "Active" if account.is_active else "Archived",
            ]

            for column_index, value in enumerate(values):
                self.m_table.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem(value),
                )

    def _create_account(self) -> None:
        """Open account creation and save accepted entries."""
        if self.m_service is None:
            return

        dialog = CreateAccountDialog(self)

        if dialog.exec() != QDialog.Accepted:
            return

        account = dialog.get_account()

        try:
            self.m_service.create_trading_account(account)

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Account Validation",
                str(error),
            )
            return

        self.refresh_accounts()
