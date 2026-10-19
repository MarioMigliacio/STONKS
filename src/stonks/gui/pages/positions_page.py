# =============================================================================
# File: positions_page.py
# Purpose: Displays and manages journal positions and performance analytics.
# =============================================================================

from decimal import Decimal
from typing import Optional

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor
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
from stonks.gui.pages.position_details_dialog import PositionDetailsDialog
from stonks.journal.analytics.position_analytics import (
    calculate_position_metrics,
)
from stonks.journal.models.position_status import PositionStatus
from stonks.journal.persistence.journal_repository import JournalRepository
from stonks.journal.services.journal_service import JournalService


class PositionsPage(QWidget):
    """
    Display and manage journal positions with performance analytics.

    Provides account-aware position history, creation, editing,
    deletion, and navigation to detailed execution records.

    Each position's metrics are calculated through the journal
    analytics engine. Archived accounts remain available for
    historical review but cannot be modified through the GUI.

    Attributes:
        m_repository:
            Journal repository used to retrieve accounts, positions,
            and execution history.

        m_service:
            Optional journal service responsible for validated writes.

        m_account_selector:
            Dropdown containing available trading accounts.

        m_create_button:
            Compact button that opens the position creation dialog.

        m_actions_button:
            Compact dropdown button for selected-position operations.

        m_actions_menu:
            Native Qt menu containing position management actions.

        m_edit_action:
            Menu action that opens position metadata for editing.

        m_delete_action:
            Menu action that deletes an empty position after confirmation.

        m_table:
            Table displaying position status, shares, and realized
            trading performance for the selected account.

        m_empty_label:
            Informational label shown when the account has no positions.
    """

    def __init__(
        self,
        repository: JournalRepository,
        service: Optional[JournalService] = None,
    ) -> None:
        """
        Initialize the trading journal positions page.

        Args:
            repository:
                Repository providing trading account and position data.

            service:
                Optional journal service for validated position operations.
        """
        super().__init__()

        self.m_repository = repository
        self.m_service = service

        self._setup_ui()
        self.refresh_accounts()

    def _setup_ui(self) -> None:
        """Construct the trading journal performance overview."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # -------------------------------------------------------------
        # Journal heading and primary actions
        # -------------------------------------------------------------
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        heading_layout = QVBoxLayout()
        heading_layout.setSpacing(4)

        title = QLabel("Trading Journal")
        title.setObjectName("journalPageTitle")

        subtitle = QLabel("Your trading performance at a glance")
        subtitle.setObjectName("journalPageSubtitle")

        heading_layout.addWidget(title)
        heading_layout.addWidget(subtitle)

        header_layout.addLayout(heading_layout)
        header_layout.addStretch()

        # Compact New Position button.
        self.m_create_button = QPushButton()
        self.m_create_button.setObjectName("journalCreateButton")
        self.m_create_button.setIcon(get_icon("plus"))
        self.m_create_button.setIconSize(QSize(20, 20))
        self.m_create_button.setFixedSize(40, 40)
        self.m_create_button.setToolTip("New Position")
        self.m_create_button.setAccessibleName("New Position")
        self.m_create_button.setEnabled(False)

        # Compact Actions menu button.
        self.m_actions_button = QPushButton()
        self.m_actions_button.setObjectName("journalActionsButton")
        self.m_actions_button.setIcon(get_icon("ellipsis-vertical"))
        self.m_actions_button.setIconSize(QSize(20, 20))
        self.m_actions_button.setFixedSize(40, 40)
        self.m_actions_button.setToolTip("Position Actions")
        self.m_actions_button.setAccessibleName("Position Actions")
        self.m_actions_button.setEnabled(False)

        # Native menu actions preserve standard Qt alignment,
        # keyboard navigation, and disabled-state behavior.
        self.m_actions_menu = QMenu(self)

        self.m_edit_action = self.m_actions_menu.addAction("Edit Position")
        self.m_edit_action.setIcon(get_icon("pencil"))
        self.m_edit_action.setEnabled(False)

        self.m_actions_menu.addSeparator()

        self.m_delete_action = self.m_actions_menu.addAction("Delete Position")
        self.m_delete_action.setIcon(get_icon("trash-danger"))
        self.m_delete_action.setEnabled(False)

        self.m_actions_button.setMenu(self.m_actions_menu)

        header_layout.addWidget(self.m_create_button)
        header_layout.addWidget(self.m_actions_button)

        layout.addLayout(header_layout)

        # -------------------------------------------------------------
        # Trading account selector
        # -------------------------------------------------------------
        account_section = QVBoxLayout()
        account_section.setSpacing(8)

        account_label = QLabel("TRADING ACCOUNT")
        account_label.setObjectName("journalAccountLabel")

        self.m_account_selector = QComboBox()
        self.m_account_selector.setObjectName("journalAccountSelector")
        self.m_account_selector.setMinimumHeight(44)

        account_section.addWidget(account_label)
        account_section.addWidget(self.m_account_selector)

        layout.addLayout(account_section)

        # -------------------------------------------------------------
        # Positions performance table
        # -------------------------------------------------------------
        self.m_table = QTableWidget()
        self.m_table.setObjectName("journalPositionsTable")

        self.m_table.setColumnCount(5)
        self.m_table.setHorizontalHeaderLabels(
            [
                "Ticker",
                "Status",
                "Shares",
                "Realized P&L",
                "Return %",
            ]
        )

        self.m_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.m_table.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.m_table.setSelectionMode(QAbstractItemView.SingleSelection)

        self.m_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.m_table.verticalHeader().setVisible(False)
        self.m_table.verticalHeader().setDefaultSectionSize(40)

        layout.addWidget(self.m_table)

        # -------------------------------------------------------------
        # Empty state
        # -------------------------------------------------------------
        self.m_empty_label = QLabel("No positions recorded for this trading account.")
        self.m_empty_label.setObjectName("emptyState")

        layout.addWidget(self.m_empty_label)

        # -------------------------------------------------------------
        # Signals
        # -------------------------------------------------------------
        self.m_account_selector.currentIndexChanged.connect(self._on_account_changed)

        self.m_create_button.clicked.connect(self._create_position)

        self.m_edit_action.triggered.connect(self._edit_position)

        self.m_delete_action.triggered.connect(self._delete_position)

        self.m_table.itemSelectionChanged.connect(self._update_action_state)

        self.m_table.itemDoubleClicked.connect(self._open_position_details)

    def refresh_accounts(self) -> None:
        """
        Reload available accounts while preserving account selection.

        Falls back to the default account if the previously selected
        account no longer exists.
        """
        previous_account_id = self.get_selected_account_id()

        accounts = self.m_repository.get_trading_accounts()

        self.m_account_selector.blockSignals(True)

        try:
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

            if selected_account_id is None or not any(
                account.account_id == selected_account_id for account in accounts
            ):
                default_account = next(
                    (account for account in accounts if account.is_default),
                    None,
                )

                selected_account_id = default_account.account_id if default_account is not None else None

            if selected_account_id is not None:
                index = self.m_account_selector.findData(selected_account_id)

                if index >= 0:
                    self.m_account_selector.setCurrentIndex(index)

        finally:
            self.m_account_selector.blockSignals(False)

        self._on_account_changed()

    def get_selected_account_id(self) -> Optional[int]:
        """
        Return the currently selected trading account identifier.

        Returns:
            Optional[int]:
                Database account ID, or None if no valid
                account is selected.
        """
        account_id = self.m_account_selector.currentData()

        return account_id if type(account_id) is int else None

    def get_selected_position_id(self) -> Optional[int]:
        """
        Return the selected journal position identifier.

        Returns:
            Optional[int]:
                Database position ID, or None when no
                valid table row is selected.
        """
        selected_rows = self.m_table.selectionModel().selectedRows()

        if not selected_rows:
            return None

        row = selected_rows[0].row()
        item = self.m_table.item(row, 0)

        if item is None:
            return None

        position_id = item.data(Qt.UserRole)

        return position_id if type(position_id) is int else None

    @staticmethod
    def _format_realized_pnl(value: Decimal) -> str:
        """
        Format realized profit or loss as signed currency.

        Args:
            value:
                Realized profit or loss from the analytics engine.

        Returns:
            str:
                Formatted currency amount with the appropriate sign.
        """
        if value > 0:
            return f"+${value:,.2f}"

        if value < 0:
            return f"-${abs(value):,.2f}"

        return "$0.00"

    @staticmethod
    def _format_return_pct(
        value: Optional[Decimal],
    ) -> str:
        """
        Format realized return as a signed percentage.

        Args:
            value:
                Realized percentage return on shares sold,
                or None if no shares have been sold.

        Returns:
            str:
                Formatted percentage or an unavailable indicator.
        """
        if value is None:
            return "—"

        return f"{value:+,.2f}%"

    def _on_account_changed(self, *_args) -> None:
        """
        Refresh displayed positions when account selection changes.

        The New Position button is enabled only when a valid,
        active trading account and journal service are available.
        """
        account_id = self.get_selected_account_id()

        account = self.m_repository.get_trading_account(account_id) if account_id is not None else None

        can_create = self.m_service is not None and account is not None and account.is_active

        self.m_create_button.setEnabled(can_create)

        self.refresh_positions()

    def refresh_positions(self) -> None:
        """
        Reload positions and their calculated performance metrics.

        Retrieves all positions belonging to the selected account,
        calculates analytics using the journal engine, and preserves
        the selected position using its persistent database ID.
        """
        account_id = self.get_selected_account_id()
        selected_position_id = self.get_selected_position_id()

        positions = self.m_repository.get_positions(account_id=account_id) if account_id is not None else []

        # Avoid intermediate selection notifications while
        # rebuilding the performance table.
        self.m_table.blockSignals(True)

        try:
            self.m_table.clearSelection()
            self.m_table.setRowCount(len(positions))

            for row_index, position in enumerate(positions):
                executions = self.m_repository.get_position_executions(position.position_id)

                metrics = calculate_position_metrics(
                    position_id=position.position_id,
                    executions=executions,
                )

                values = [
                    position.ticker,
                    metrics.status.value,
                    format(metrics.open_shares, "f"),
                    self._format_realized_pnl(metrics.realized_pnl),
                    self._format_return_pct(metrics.realized_return_pct),
                ]

                for column_index, value in enumerate(values):
                    item = QTableWidgetItem(value)

                    # Preserve the position ID for selection,
                    # editing, deletion, and drill-down navigation.
                    item.setData(
                        Qt.UserRole,
                        position.position_id,
                    )

                    # Ticker is our primary row identifier.
                    if column_index == 0:
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)

                    # Position lifecycle status.
                    elif column_index == 1:
                        item.setTextAlignment(Qt.AlignCenter)

                        if metrics.status == PositionStatus.OPEN:
                            item.setForeground(QColor("#4ADE80"))

                        elif metrics.status == PositionStatus.CLOSED:
                            item.setForeground(QColor("#A9B5C6"))

                    # Remaining shares.
                    elif column_index == 2:
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

                    # Realized profit and return percentage.
                    elif column_index in (3, 4):
                        performance = metrics.realized_pnl if column_index == 3 else metrics.realized_return_pct

                        if performance is not None:
                            if performance > 0:
                                item.setForeground(QColor("#4ADE80"))

                            elif performance < 0:
                                item.setForeground(QColor("#F87171"))

                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)

                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

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

        finally:
            self.m_table.blockSignals(False)

        self.m_empty_label.setVisible(len(positions) == 0)

        self._update_action_state()

    def _update_action_state(self) -> None:
        """
        Update position management actions based on selection.

        Editing is permitted only for positions belonging to
        active accounts. Positions containing executions cannot
        be deleted.
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
        """
        Create a new position for the selected trading account.

        Validates account activity before displaying the form
        and delegates persistence to the journal service.
        """
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
        """
        Edit the metadata of the selected journal position.

        Prevents editing positions outside the selected account
        or belonging to archived trading accounts.
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
        Delete an empty journal position after confirmation.

        Prevents deletion of positions belonging to archived
        accounts or containing trade execution history.
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

    def _open_position_details(self, _item=None) -> None:
        """
        Open execution history and analytics for a selected position.

        Archived accounts remain accessible for historical review.
        Refreshes the overview after closing the details dialog
        to reflect any changes to execution history.

        Args:
            _item:
                Optional table item provided by the double-click signal.
        """
        position_id = self.get_selected_position_id()

        if position_id is None:
            return

        position = self.m_repository.get_position(position_id)

        if position is None:
            self.refresh_positions()
            return

        if position.account_id != self.get_selected_account_id():
            self.refresh_positions()
            return

        dialog = PositionDetailsDialog(
            position_id=position_id,
            repository=self.m_repository,
            service=self.m_service,
            parent=self,
        )

        dialog.exec()

        # Execution changes alter status, shares, P&L, and return.
        self.refresh_positions()
