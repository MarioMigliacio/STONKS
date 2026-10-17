# =============================================================================
# File: positions_page.py
# Purpose: Displays and manages journal positions by trading account.
# =============================================================================

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
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
from stonks.gui.pages.create_position_dialog import CreatePositionDialog
from stonks.gui.pages.delete_position_dialog import DeletePositionDialog
from stonks.journal.persistence.journal_repository import JournalRepository
from stonks.journal.services.journal_service import JournalService


class PositionsPage(QWidget):
    """
    Display and manage journal positions for a selected trading account.

    Provides account-aware position history, creation, editing,
    and guarded deletion. Archived accounts remain available
    for historical review but cannot be modified through the GUI.

    Attributes:
        m_repository:
            Journal repository used to retrieve accounts and positions.

        m_service:
            Optional journal service responsible for validated operations.

        m_account_selector:
            Dropdown containing available trading accounts.

        m_create_button:
            Button that opens the new position entry dialog.

        m_actions_button:
            Dropdown button providing selected-position operations.

        m_actions_menu:
            Context menu containing position management actions.

        m_edit_action:
            Menu action that opens the position editing dialog.

        m_delete_action:
            Menu action that deletes an empty position after confirmation.

        m_table:
            Table displaying positions belonging to the selected account.

        m_empty_label:
            Informational label shown when no positions exist.
    """

    def __init__(
        self,
        repository: JournalRepository,
        service: Optional[JournalService] = None,
    ) -> None:
        """Initialize the positions page and load journal data."""
        super().__init__()

        self.m_repository = repository
        self.m_service = service

        self._setup_ui()
        self.refresh_accounts()

    def _setup_ui(self) -> None:
        """Construct the trading journal overview interface."""
        layout = QVBoxLayout(self)

        # Page header.
        header_layout = QHBoxLayout()

        title = QLabel("Trading Journal")
        title.setObjectName("pageTitle")

        self.m_create_button = QPushButton("New Position")
        self.m_create_button.setIcon(get_icon("plus"))
        self.m_create_button.setEnabled(False)

        self.m_actions_button = QPushButton("Actions")
        self.m_actions_button.setEnabled(False)

        # Position actions menu.
        self.m_actions_menu = QMenu(self)

        self.m_edit_action = self.m_actions_menu.addAction("Edit Position")
        self.m_edit_action.setIcon(get_icon("pencil"))

        self.m_actions_menu.addSeparator()

        self.m_delete_action = self.m_actions_menu.addAction("Delete Position")
        self.m_delete_action.setIcon(get_icon("trash-danger"))

        self.m_actions_button.setMenu(self.m_actions_menu)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.m_create_button)
        header_layout.addWidget(self.m_actions_button)

        layout.addLayout(header_layout)

        # Trading account selector.
        account_label = QLabel("Trading Account")

        self.m_account_selector = QComboBox()
        self.m_account_selector.currentIndexChanged.connect(self._on_account_changed)

        layout.addWidget(account_label)
        layout.addWidget(self.m_account_selector)

        # Positions table.
        self.m_table = QTableWidget()
        self.m_table.setColumnCount(4)

        self.m_table.setHorizontalHeaderLabels(
            [
                "Ticker",
                "Strategy",
                "Catalyst",
                "Position ID",
            ]
        )

        self.m_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.m_table.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.m_table.setSelectionMode(QAbstractItemView.SingleSelection)

        self.m_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.m_table.itemSelectionChanged.connect(self._update_action_state)

        layout.addWidget(self.m_table)

        # Empty state.
        self.m_empty_label = QLabel("No positions recorded for this trading account.")
        self.m_empty_label.setObjectName("emptyState")

        layout.addWidget(self.m_empty_label)

        # Connect actions.
        self.m_create_button.clicked.connect(self._create_position)
        self.m_edit_action.triggered.connect(self._edit_position)
        self.m_delete_action.triggered.connect(self._delete_position)

    def refresh_accounts(self) -> None:
        """
        Reload account choices while preserving the selected account.

        Falls back to the default account when the previous
        selection is unavailable.
        """
        previous_account_id = self.get_selected_account_id()
        accounts = self.m_repository.get_trading_accounts()

        self.m_account_selector.blockSignals(True)
        self.m_account_selector.clear()

        for account in accounts:
            display_name = account.name

            if not account.is_active:
                display_name += " (Archived)"

            self.m_account_selector.addItem(
                display_name,
                userData=account.account_id,
            )

        selected_account_id = previous_account_id

        if selected_account_id is None or not any(account.account_id == selected_account_id for account in accounts):
            default_account = next(
                (account for account in accounts if account.is_default),
                None,
            )

            selected_account_id = default_account.account_id if default_account is not None else None

        if selected_account_id is not None:
            index = self.m_account_selector.findData(selected_account_id)

            if index >= 0:
                self.m_account_selector.setCurrentIndex(index)

        self.m_account_selector.blockSignals(False)

        self._on_account_changed()

    def get_selected_account_id(self) -> Optional[int]:
        """Return the selected trading account's database identifier."""
        account_id = self.m_account_selector.currentData()

        return account_id if type(account_id) is int else None

    def get_selected_position_id(self) -> Optional[int]:
        """Return the selected journal position's database identifier."""
        selected_rows = self.m_table.selectionModel().selectedRows()

        if not selected_rows:
            return None

        row = selected_rows[0].row()
        item = self.m_table.item(row, 0)

        if item is None:
            return None

        position_id = item.data(Qt.UserRole)

        return position_id if type(position_id) is int else None

    def _on_account_changed(self, *_args) -> None:
        """Refresh positions and controls after account selection."""
        account_id = self.get_selected_account_id()

        account = self.m_repository.get_trading_account(account_id) if account_id is not None else None

        can_create = self.m_service is not None and account is not None and account.is_active

        self.m_create_button.setEnabled(can_create)

        self.refresh_positions()

    def refresh_positions(self) -> None:
        """Reload positions while preserving selection when possible."""
        account_id = self.get_selected_account_id()
        selected_position_id = self.get_selected_position_id()

        positions = self.m_repository.get_positions(account_id=account_id) if account_id is not None else []

        # Clear the previous selection before repopulating rows.
        self.m_table.clearSelection()
        self.m_table.setRowCount(len(positions))

        for row_index, position in enumerate(positions):
            values = [
                position.ticker,
                position.strategy,
                position.catalyst,
                str(position.position_id),
            ]

            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)

                item.setData(
                    Qt.UserRole,
                    position.position_id,
                )

                self.m_table.setItem(
                    row_index,
                    column_index,
                    item,
                )

        # Restore selection using the persistent position ID.
        if selected_position_id is not None:
            for row in range(self.m_table.rowCount()):
                item = self.m_table.item(row, 0)

                if item is not None and item.data(Qt.UserRole) == selected_position_id:
                    self.m_table.selectRow(row)
                    break

        self.m_empty_label.setVisible(len(positions) == 0)

        self._update_action_state()

    def _update_action_state(self) -> None:
        """
        Update position management actions based on selected records.

        Archived accounts cannot be modified, and positions
        containing trade executions cannot be deleted.
        """
        account_id = self.get_selected_account_id()
        position_id = self.get_selected_position_id()

        account = self.m_repository.get_trading_account(account_id) if account_id is not None else None

        position = self.m_repository.get_position(position_id) if position_id is not None else None

        can_manage = (
            self.m_service is not None
            and account is not None
            and account.is_active
            and position is not None
            and position.account_id == account_id
        )

        self.m_actions_button.setEnabled(can_manage)
        self.m_edit_action.setEnabled(can_manage)

        can_delete = can_manage and not self.m_repository.get_position_executions(position_id)

        self.m_delete_action.setEnabled(can_delete)

    def _create_position(self) -> None:
        """Create a position for the selected trading account."""
        if self.m_service is None:
            return

        account_id = self.get_selected_account_id()

        if account_id is None:
            return

        account = self.m_repository.get_trading_account(account_id)

        if account is None or not account.is_active:
            QMessageBox.warning(
                self,
                "Trading Account",
                "Select an active trading account before creating a position.",
            )
            self.refresh_accounts()
            return

        dialog = CreatePositionDialog(
            account_id=account_id,
            account_name=account.name,
            parent=self,
        )

        if dialog.exec() != QDialog.Accepted:
            return

        try:
            self.m_service.create_position(dialog.get_position())

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Position Validation",
                str(error),
            )
            return

        self.refresh_positions()

    def _edit_position(self) -> None:
        """Edit the selected position through the journal service."""
        if self.m_service is None:
            return

        position_id = self.get_selected_position_id()

        if position_id is None:
            return

        position = self.m_repository.get_position(position_id)

        if position is None:
            QMessageBox.warning(
                self,
                "Position Not Found",
                "The selected position no longer exists.",
            )
            self.refresh_positions()
            return

        account_id = self.get_selected_account_id()

        if position.account_id != account_id:
            self.refresh_positions()
            return

        account = self.m_repository.get_trading_account(position.account_id)

        if account is None or not account.is_active:
            QMessageBox.warning(
                self,
                "Trading Account",
                "Positions belonging to inactive accounts cannot be edited.",
            )
            self.refresh_accounts()
            return

        dialog = CreatePositionDialog(
            account_id=account.account_id,
            account_name=account.name,
            parent=self,
            position=position,
        )

        if dialog.exec() != QDialog.Accepted:
            return

        try:
            updated = self.m_service.update_position(dialog.get_position())

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Position Validation",
                str(error),
            )
            return

        if not updated:
            QMessageBox.warning(
                self,
                "Position Not Found",
                "The selected position could not be updated.",
            )

        self.refresh_positions()

    def _delete_position(self) -> None:
        """
        Delete an empty journal position after explicit confirmation.

        Positions containing executions are protected by the
        journal service and cannot be deleted through this workflow.
        """
        if self.m_service is None:
            return

        position_id = self.get_selected_position_id()

        if position_id is None:
            return

        position = self.m_repository.get_position(position_id)

        if position is None:
            QMessageBox.warning(
                self,
                "Position Not Found",
                "The selected position no longer exists.",
            )
            self.refresh_positions()
            return

        account_id = self.get_selected_account_id()

        if position.account_id != account_id:
            self.refresh_positions()
            return

        account = self.m_repository.get_trading_account(position.account_id)

        if account is None or not account.is_active:
            QMessageBox.warning(
                self,
                "Trading Account",
                "Positions belonging to inactive accounts cannot be deleted.",
            )
            self.refresh_accounts()
            return

        # The service enforces this restriction again at deletion time.
        if self.m_repository.get_position_executions(position_id):
            QMessageBox.warning(
                self,
                "Position Deletion",
                "Cannot delete a position containing trade executions.",
            )
            self.refresh_positions()
            return

        dialog = DeletePositionDialog(
            position=position,
            parent=self,
        )

        if dialog.exec() != QDialog.Accepted:
            return

        try:
            deleted = self.m_service.delete_position(position_id)

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Position Deletion",
                str(error),
            )
            self.refresh_positions()
            return

        if not deleted:
            QMessageBox.warning(
                self,
                "Position Not Found",
                "The position could not be deleted.",
            )

        self.refresh_positions()
