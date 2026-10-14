# =============================================================================
# File: accounts_page.py
# Purpose: Display and manage trading accounts in the STONKS GUI.
# =============================================================================

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
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
        self.m_table.setColumnCount(5)

        self.m_table.setHorizontalHeaderLabels(["Name", "Type", "Broker", "Status", "Default"])

        self.m_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.m_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.m_table.setSelectionMode(QAbstractItemView.SingleSelection)

        self.m_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.m_empty_label = QLabel("No trading accounts yet. Create your first account to begin.")
        self.m_empty_label.setObjectName("emptyState")

        layout.addWidget(self.m_table)
        layout.addWidget(self.m_empty_label)

    def refresh_accounts(self) -> None:
        """Retrieve trading accounts and refresh the display."""
        accounts = self.m_repository.get_trading_accounts()
        selected_account_id = self.get_selected_account_id()
        self.m_table.clearSelection()

        self.m_table.setRowCount(len(accounts))
        self.m_empty_label.setVisible(len(accounts) == 0)

        for row_index, account in enumerate(accounts):
            values = [
                account.name,
                account.account_type.value.replace("_", " ").title(),
                account.broker,
                "Active" if account.is_active else "Archived",
                "★ Yes" if account.is_default else "—",
            ]

            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)

                # Store the database ID independently of its table row.
                item.setData(
                    Qt.UserRole,
                    account.account_id,
                )

                if column_index == 4 and account.is_default:
                    item.setForeground(QColor("#59A8FF"))

                self.m_table.setItem(
                    row_index,
                    column_index,
                    item,
                )

        if selected_account_id is not None:
            for row_index in range(self.m_table.rowCount()):
                item = self.m_table.item(row_index, 0)

                if item is not None and item.data(Qt.UserRole) == selected_account_id:
                    self.m_table.selectRow(row_index)
                    break

    def get_selected_account_id(self) -> Optional[int]:
        """
        Retrieve the database identifier of the selected account.

        Returns:
            Optional[int]:
                Selected account identifier, or None if no
                account is selected.
        """
        selected_rows = self.m_table.selectionModel().selectedRows()

        if not selected_rows:
            return None

        row_index = selected_rows[0].row()

        item = self.m_table.item(row_index, 0)

        if item is None:
            return None

        account_id = item.data(Qt.UserRole)

        return account_id if type(account_id) is int else None

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
