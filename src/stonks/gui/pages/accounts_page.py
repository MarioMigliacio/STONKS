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
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from stonks.gui.icons import get_icon
from stonks.gui.pages.create_account_dialog import CreateAccountDialog
from stonks.journal.persistence.journal_repository import JournalRepository
from stonks.journal.services.journal_service import JournalService


class AccountsPage(QWidget):
    """
    Display and manage trading accounts within the STONKS journal.

    Provides a table of trading accounts, including their account type,
    broker, active status, and default designation. Supports creating,
    editing, selecting a default account, and archiving accounts as
    well as reactivating archived accounts through the journal service.

    Attributes:
        m_repository:
            Journal repository used to retrieve trading account data.

        m_service:
            Optional journal service responsible for validated account
            operations, including creation, updates, default selection,
            and archival.

        m_create_button:
            Button that opens the dialog for creating a trading account.

        m_actions_button:
            Dropdown button providing account management operations
            for the currently selected trading account.

        m_actions_menu:
            Context menu containing the available account management
            actions.

        m_edit_action:
            Menu action that opens the selected account for editing.

        m_default_action:
            Menu action that assigns the selected active account as
            the default trading account.

        m_archive_action:
            Menu action that archives the selected non-default account
            while preserving its trading history.

        m_reactivate_action:
            Menu action that restores an archived trading account
            to active status without modifying its historical records
            or default designation.

        m_table:
            Table displaying trading account information and managing
            the currently selected account.

        m_empty_label:
            Informational label displayed when no trading accounts
            exist in the journal.
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
                Optional service used for validated account operations.
        """
        super().__init__()

        self.m_repository = repository
        self.m_service = service

        self._setup_ui()
        self.refresh_accounts()

    def _setup_ui(self) -> None:
        """Construct the trading account management interface."""
        layout = QVBoxLayout(self)

        # Page header.
        header_layout = QHBoxLayout()

        title = QLabel("Trading Accounts")
        title.setObjectName("pageTitle")

        self.m_create_button = QPushButton("New Account")
        self.m_create_button.setEnabled(self.m_service is not None)
        self.m_create_button.clicked.connect(self._create_account)

        # Account actions menu.
        self.m_actions_button = QPushButton("Actions")
        self.m_actions_button.setEnabled(False)

        self.m_actions_menu = QMenu(self)
        self.m_edit_action = self.m_actions_menu.addAction("Edit Account")
        self.m_edit_action.setIcon(get_icon("pencil"))

        self.m_default_action = self.m_actions_menu.addAction("Set as Default")
        self.m_default_action.setIcon(get_icon("star"))

        self.m_actions_menu.addSeparator()

        self.m_archive_action = self.m_actions_menu.addAction("Archive Account")
        self.m_archive_action.setIcon(get_icon("archive"))

        self.m_reactivate_action = self.m_actions_menu.addAction("Reactivate Account")
        self.m_reactivate_action.setIcon(get_icon("archive-restore"))
        self.m_reactivate_action.setVisible(False)

        self.m_actions_button.setMenu(self.m_actions_menu)
        self.m_edit_action.triggered.connect(self._edit_account)
        self.m_default_action.triggered.connect(self._set_default_account)
        self.m_archive_action.triggered.connect(self._archive_account)
        self.m_reactivate_action.triggered.connect(self._reactivate_account)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.m_create_button)
        header_layout.addWidget(self.m_actions_button)

        layout.addLayout(header_layout)

        # Trading accounts table.
        self.m_table = QTableWidget()
        self.m_table.setColumnCount(5)
        self.m_table.setHorizontalHeaderLabels(["Name", "Type", "Broker", "Status", "Default"])

        self.m_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.m_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.m_table.setSelectionMode(QAbstractItemView.SingleSelection)

        self.m_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.m_table.itemSelectionChanged.connect(self._update_action_state)

        # Empty database message.
        self.m_empty_label = QLabel("No trading accounts yet. Create your first account to begin.")
        self.m_empty_label.setObjectName("emptyState")

        layout.addWidget(self.m_table)
        layout.addWidget(self.m_empty_label)

    def refresh_accounts(self) -> None:
        """Retrieve trading accounts and refresh the display."""
        selected_account_id = self.get_selected_account_id()

        accounts = self.m_repository.get_trading_accounts()

        if selected_account_id is None:
            default_account = next(
                (account for account in accounts if account.is_default),
                None,
            )

            if default_account is not None:
                selected_account_id = default_account.account_id

        self.m_table.setRowCount(len(accounts))

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

                # Store account identity independently of row position.
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

        self.m_empty_label.setVisible(len(accounts) == 0)

        # Restore the previously selected account after refreshing.
        if selected_account_id is not None:
            for row_index in range(self.m_table.rowCount()):
                item = self.m_table.item(row_index, 0)

                if item is not None and item.data(Qt.UserRole) == selected_account_id:
                    self.m_table.selectRow(row_index)
                    break

        self._update_action_state()

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

    def _update_action_state(self) -> None:
        """Update available actions for the selected trading account."""
        account_id = self.get_selected_account_id()

        has_selection = self.m_service is not None and account_id is not None

        self.m_actions_button.setEnabled(has_selection)

        if not has_selection:
            self.m_default_action.setEnabled(False)

            self.m_archive_action.setVisible(True)
            self.m_archive_action.setEnabled(False)

            self.m_reactivate_action.setVisible(False)
            self.m_reactivate_action.setEnabled(False)
            return

        account = self.m_repository.get_trading_account(account_id)

        if account is None:
            self.m_actions_button.setEnabled(False)
            self.m_default_action.setEnabled(False)
            self.m_archive_action.setEnabled(False)
            self.m_reactivate_action.setEnabled(False)
            return

        self.m_default_action.setEnabled(account.is_active and not account.is_default)

        self.m_archive_action.setVisible(account.is_active)
        self.m_archive_action.setEnabled(account.is_active and not account.is_default)

        self.m_reactivate_action.setVisible(not account.is_active)
        self.m_reactivate_action.setEnabled(not account.is_active)

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

    def _edit_account(self) -> None:
        """Edit the selected trading account through the journal service."""
        if self.m_service is None:
            return

        account_id = self.get_selected_account_id()

        if account_id is None:
            return

        account = self.m_repository.get_trading_account(account_id)

        if account is None:
            QMessageBox.warning(
                self,
                "Account Not Found",
                "The selected account no longer exists.",
            )
            self.refresh_accounts()
            return

        dialog = CreateAccountDialog(self, account=account)

        if dialog.exec() != QDialog.Accepted:
            return

        updated_account = dialog.get_account()

        try:
            updated = self.m_service.update_trading_account(updated_account)

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Account Validation",
                str(error),
            )
            return

        if not updated:
            QMessageBox.warning(
                self,
                "Account Not Found",
                "The account could not be updated.",
            )
            self.refresh_accounts()
            return

        self.refresh_accounts()

    def _set_default_account(self) -> None:
        """Assign the selected trading account as the default."""
        if self.m_service is None:
            return

        account_id = self.get_selected_account_id()

        if account_id is None:
            return

        try:
            self.m_service.set_default_trading_account(account_id)

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Default Account",
                str(error),
            )
            self.refresh_accounts()
            return

        self.refresh_accounts()

    def _archive_account(self) -> None:
        """
        Archive the selected trading account after user confirmation.

        Archiving marks the account as inactive while preserving its
        positions, executions, transactions, and historical records.
        """
        if self.m_service is None:
            return

        account_id = self.get_selected_account_id()

        if account_id is None:
            return

        account = self.m_repository.get_trading_account(account_id)

        if account is None:
            QMessageBox.warning(
                self,
                "Account Not Found",
                "The selected account no longer exists.",
            )
            self.refresh_accounts()
            return

        response = QMessageBox.question(
            self,
            "Archive Trading Account",
            (
                f"Archive '{account.name}'?\n\n"
                "This account will become inactive.\n"
                "Its trading history and financial records will be preserved.\n\n"
                "You can reactivate this account later."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if response != QMessageBox.Yes:
            return

        try:
            archived = self.m_service.archive_trading_account(account_id)

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Account Archival",
                str(error),
            )
            self.refresh_accounts()
            return

        if not archived:
            QMessageBox.warning(
                self,
                "Account Not Found",
                "The account could not be archived.",
            )

        self.refresh_accounts()

    def _reactivate_account(self) -> None:
        """
        Reactivate the selected archived trading account.

        Restores the account's active status through the journal
        service and refreshes the displayed account information.
        """
        if self.m_service is None:
            return

        account_id = self.get_selected_account_id()

        if account_id is None:
            return

        try:
            reactivated = self.m_service.reactivate_trading_account(account_id)

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Account Reactivation",
                str(error),
            )
            self.refresh_accounts()
            return

        if not reactivated:
            QMessageBox.warning(
                self,
                "Account Not Found",
                "The selected account could not be reactivated.",
            )

        self.refresh_accounts()
