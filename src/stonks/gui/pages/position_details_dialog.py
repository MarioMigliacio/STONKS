# =============================================================================
# File: position_details_dialog.py
# Purpose: Displays position details and manages trade execution history.
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
)

from stonks.gui.icons import get_icon
from stonks.gui.pages.add_execution_dialog import AddExecutionDialog
from stonks.gui.pages.delete_execution_dialog import DeleteExecutionDialog
from stonks.gui.widgets.position_metrics_widget import PositionMetricsWidget
from stonks.journal.analytics.position_analytics import (
    calculate_position_metrics,
)
from stonks.journal.models.execution_side import ExecutionSide
from stonks.journal.persistence.journal_repository import JournalRepository
from stonks.journal.services.journal_service import JournalService


class PositionDetailsDialog(QDialog):
    """
    Display position metadata and manage its trade execution history.

    Retrieves persisted position information and chronological BUY/SELL
    executions. Supports creating, editing, and deleting executions through
    the journal service while protecting archived trading accounts.

    Attributes:
        m_position_id:
            Identifier of the position being displayed.

        m_repository:
            Repository providing persisted positions, trading accounts,
            and execution history.

        m_service:
            Optional journal service used for validated execution writes.

        m_title:
            Heading identifying the current trading position.

        m_metadata_label:
            Label displaying position strategy, catalyst, and entry reason.

        m_metrics_widget:
            Positional Metrics widget for display.

        m_add_execution_button:
            Button opening the execution creation dialog.

        m_actions_button:
            Dropdown button containing execution management actions.

        m_actions_menu:
            Menu containing Edit Execution and Delete Execution.

        m_edit_action:
            Action opening the selected execution for editing.

        m_delete_action:
            Action for deleting the selected execution after confirmation.

        m_executions_table:
            Table showing chronological execution history.

        m_empty_label:
            Informational label shown when the position has no executions.

        m_close_button:
            Button closing the position details dialog.
    """

    def __init__(
        self,
        position_id: int,
        repository: JournalRepository,
        service: Optional[JournalService] = None,
        parent=None,
    ) -> None:
        """
        Initialize the position details dialog.

        Args:
            position_id:
                Identifier of the position to display.

            repository:
                Journal repository used for data retrieval.

            service:
                Optional journal service for validated execution operations.

            parent:
                Optional parent Qt widget.
        """
        super().__init__(parent)

        self.m_position_id = position_id
        self.m_repository = repository
        self.m_service = service

        self.setWindowTitle("Position Details")
        self.resize(900, 800)
        self.setMinimumSize(750, 500)

        self._setup_ui()
        self.refresh_details()

    def _setup_ui(self) -> None:
        """Construct the position details and execution management UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # -------------------------------------------------------------
        # Position heading and metadata
        # -------------------------------------------------------------
        self.m_title = QLabel("Position Details")
        self.m_title.setObjectName("pageTitle")

        layout.addWidget(self.m_title)

        self.m_metadata_label = QLabel()
        self.m_metadata_label.setWordWrap(True)

        layout.addWidget(self.m_metadata_label)

        self.m_metrics_widget = PositionMetricsWidget(self)
        layout.addWidget(self.m_metrics_widget)

        # -------------------------------------------------------------
        # Execution management controls
        # -------------------------------------------------------------
        header_layout = QHBoxLayout()

        heading = QLabel("Trade Executions")
        heading.setObjectName("pageTitle")

        self.m_add_execution_button = QPushButton("Add Execution")
        self.m_add_execution_button.setIcon(get_icon("plus"))
        self.m_add_execution_button.setEnabled(False)

        self.m_actions_button = QPushButton("Actions")
        self.m_actions_button.setEnabled(False)

        self.m_actions_menu = QMenu(self)

        self.m_edit_action = self.m_actions_menu.addAction("Edit Execution")
        self.m_edit_action.setIcon(get_icon("pencil"))
        self.m_edit_action.setEnabled(False)

        self.m_actions_menu.addSeparator()

        self.m_delete_action = self.m_actions_menu.addAction("Delete Execution")
        self.m_delete_action.setIcon(get_icon("trash-danger"))

        # Actions remain disabled until a valid editable row is selected.
        self.m_delete_action.setEnabled(False)

        self.m_actions_button.setMenu(self.m_actions_menu)

        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.m_add_execution_button)
        header_layout.addWidget(self.m_actions_button)

        layout.addLayout(header_layout)

        # -------------------------------------------------------------
        # Execution history table
        # -------------------------------------------------------------
        self.m_executions_table = QTableWidget()
        self.m_executions_table.setColumnCount(7)

        self.m_executions_table.setHorizontalHeaderLabels(
            [
                "Date / Time (UTC)",
                "Side",
                "Shares",
                "Price",
                "Fees",
                "Value",
                "Execution ID",
            ]
        )

        self.m_executions_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.m_executions_table.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.m_executions_table.setSelectionMode(QAbstractItemView.SingleSelection)

        # Allow users to resize columns manually.
        header = self.m_executions_table.horizontalHeader()

        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setMinimumSectionSize(60)

        column_widths = {
            0: 175,  # Date / Time (UTC)
            1: 70,  # Side
            2: 90,  # Shares
            3: 110,  # Price
            4: 90,  # Fees
            5: 120,  # Value
            6: 110,  # Execution ID
        }

        for column, width in column_widths.items():
            self.m_executions_table.setColumnWidth(
                column,
                width,
            )

        self.m_executions_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        layout.addWidget(self.m_executions_table)

        # -------------------------------------------------------------
        # Empty state
        # -------------------------------------------------------------
        self.m_empty_label = QLabel("No trade executions recorded for this position.")
        self.m_empty_label.setObjectName("emptyState")

        layout.addWidget(self.m_empty_label)

        # -------------------------------------------------------------
        # Footer
        # -------------------------------------------------------------
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        self.m_close_button = QPushButton("Close")
        self.m_close_button.clicked.connect(self.accept)

        footer_layout.addWidget(self.m_close_button)
        layout.addLayout(footer_layout)

        # -------------------------------------------------------------
        # Signals
        # -------------------------------------------------------------
        self.m_add_execution_button.clicked.connect(self._add_execution)

        self.m_executions_table.itemSelectionChanged.connect(self._update_action_state)
        self.m_executions_table.itemDoubleClicked.connect(self._on_execution_double_clicked)

        self.m_edit_action.triggered.connect(self._edit_execution)

        self.m_delete_action.triggered.connect(self._delete_execution)

    def get_selected_execution_id(self) -> Optional[int]:
        """
        Return the database identifier of the selected execution.

        Returns:
            Optional[int]:
                Selected execution ID, or None if no valid row
                is selected.
        """
        selected_rows = self.m_executions_table.selectionModel().selectedRows()

        if not selected_rows:
            return None

        row = selected_rows[0].row()

        item = self.m_executions_table.item(
            row,
            0,
        )

        if item is None:
            return None

        execution_id = item.data(Qt.UserRole)

        return execution_id if type(execution_id) is int else None

    def _update_action_state(self) -> None:
        """
        Update execution action availability.

        Editing is permitted only when an execution is selected,
        belongs to the displayed position, and its trading account
        remains active.
        """
        execution_id = self.get_selected_execution_id()

        position = self.m_repository.get_position(self.m_position_id)

        execution = self.m_repository.get_execution(execution_id) if execution_id is not None else None

        account = (
            self.m_repository.get_trading_account(position.account_id)
            if position is not None and position.account_id is not None
            else None
        )

        can_edit = (
            self.m_service is not None
            and position is not None
            and execution is not None
            and execution.position_id == self.m_position_id
            and account is not None
            and account.is_active
        )

        self.m_actions_button.setEnabled(can_edit)
        self.m_edit_action.setEnabled(can_edit)
        self.m_delete_action.setEnabled(can_edit)

    def refresh_details(self) -> None:
        """
        Reload position metadata and execution history.

        Preserves the selected execution by database ID when
        the record remains present after refreshing.
        """
        selected_execution_id = self.get_selected_execution_id()

        position = self.m_repository.get_position(self.m_position_id)

        if position is None:
            self.m_title.setText("Position Not Found")
            self.m_metadata_label.setText("This position no longer exists.")

            self.m_executions_table.setRowCount(0)
            self.m_empty_label.setVisible(False)
            self.m_add_execution_button.setEnabled(False)
            self.m_actions_button.setEnabled(False)
            self.m_edit_action.setEnabled(False)
            self.m_delete_action.setEnabled(False)
            self.m_metrics_widget.hide()
            return

        # -------------------------------------------------------------
        # Position metadata
        # -------------------------------------------------------------
        self.m_title.setText(f"{position.ticker} — Position Details")

        self.m_metadata_label.setText(
            f"Strategy: {position.strategy or '—'}\n"
            f"Catalyst: {position.catalyst or '—'}\n"
            f"Entry Reason: {position.entry_reason or '—'}"
        )

        # -------------------------------------------------------------
        # Account permissions
        # -------------------------------------------------------------
        account = (
            self.m_repository.get_trading_account(position.account_id) if position.account_id is not None else None
        )

        can_add_execution = self.m_service is not None and account is not None and account.is_active

        self.m_add_execution_button.setEnabled(can_add_execution)

        # -------------------------------------------------------------
        # Execution history
        # -------------------------------------------------------------
        executions = self.m_repository.get_position_executions(self.m_position_id)

        metrics = calculate_position_metrics(
            position_id=self.m_position_id,
            executions=executions,
        )

        self.m_metrics_widget.update_metrics(metrics)

        # Avoid processing intermediate selection changes while
        # rebuilding the table.
        self.m_executions_table.blockSignals(True)

        try:
            self.m_executions_table.clearSelection()
            self.m_executions_table.setRowCount(len(executions))

            for row_index, execution in enumerate(executions):
                values = [
                    execution.executed_at.strftime("%Y-%m-%d %H:%M:%S"),
                    execution.side.value,
                    str(execution.shares),
                    f"${execution.price:,.4f}",
                    f"${execution.fees:,.2f}",
                    f"${execution.gross_value:,.2f}",
                    str(execution.execution_id),
                ]

                for column_index, value in enumerate(values):
                    item = QTableWidgetItem(value)

                    item.setData(
                        Qt.UserRole,
                        execution.execution_id,
                    )

                    # Highlight execution direction for quick visual scanning.
                    if column_index == 1:
                        if execution.side == ExecutionSide.BUY:
                            item.setForeground(QColor("#4ADE80"))

                        elif execution.side == ExecutionSide.SELL:
                            item.setForeground(QColor("#F87171"))

                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)

                        item.setTextAlignment(Qt.AlignCenter)

                    elif column_index in (2, 3, 4, 5):
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

                    self.m_executions_table.setItem(
                        row_index,
                        column_index,
                        item,
                    )

            # Restore selection using the persistent execution ID.
            if selected_execution_id is not None:
                for row in range(self.m_executions_table.rowCount()):
                    item = self.m_executions_table.item(
                        row,
                        0,
                    )

                    if item is not None and item.data(Qt.UserRole) == selected_execution_id:
                        self.m_executions_table.selectRow(row)
                        break

        finally:
            self.m_executions_table.blockSignals(False)

        self.m_empty_label.setVisible(len(executions) == 0)

        self._update_action_state()

    def _add_execution(self) -> None:
        """
        Create an execution for the displayed position.

        Rechecks the trading account's active status and
        delegates persistence to the journal service.
        """
        if self.m_service is None:
            return

        position = self.m_repository.get_position(self.m_position_id)

        if position is None:
            self.m_metrics_widget.hide()
            self.refresh_details()
            return

        account = (
            self.m_repository.get_trading_account(position.account_id) if position.account_id is not None else None
        )

        if account is None or not account.is_active:
            QMessageBox.warning(
                self,
                "Trading Account",
                "An active trading account is required to add executions.",
            )
            self.refresh_details()
            return

        dialog = AddExecutionDialog(
            position_id=self.m_position_id,
            ticker=position.ticker,
            parent=self,
        )

        if dialog.exec() != QDialog.Accepted:
            return

        try:
            self.m_service.create_execution(dialog.get_execution())

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Execution Validation",
                str(error),
            )
            return

        self.refresh_details()

    def _on_execution_double_clicked(self, item: QTableWidgetItem) -> None:
        """Edit the clicked execution when editing is permitted.

        Args:
            item:
                Table item that received the double-click.
        """
        if item is None:
            return

        self.m_executions_table.selectRow(item.row())
        self._update_action_state()

        if self.m_edit_action.isEnabled():
            self._edit_execution()

    def _edit_execution(self) -> None:
        """
        Edit the selected execution while preserving position identity.

        Validates the parent trading account and delegates the
        update to the journal service, which revalidates the
        complete execution history.
        """
        if self.m_service is None:
            return

        execution_id = self.get_selected_execution_id()

        if execution_id is None:
            return

        execution = self.m_repository.get_execution(execution_id)

        position = self.m_repository.get_position(self.m_position_id)

        # Protect against stale selections and mismatched ownership.
        if execution is None or position is None or execution.position_id != self.m_position_id:
            self.refresh_details()
            return

        account = (
            self.m_repository.get_trading_account(position.account_id) if position.account_id is not None else None
        )

        if account is None or not account.is_active:
            QMessageBox.warning(
                self,
                "Trading Account",
                "Archived trading accounts are read-only.",
            )
            self.refresh_details()
            return

        dialog = AddExecutionDialog(
            position_id=self.m_position_id,
            ticker=position.ticker,
            execution=execution,
            parent=self,
        )

        if dialog.exec() != QDialog.Accepted:
            return

        try:
            updated = self.m_service.update_execution(dialog.get_execution())

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Execution Validation",
                str(error),
            )
            return

        if not updated:
            QMessageBox.warning(
                self,
                "Execution Not Found",
                "The selected execution could not be updated.",
            )

        self.refresh_details()

    def _delete_execution(self) -> None:
        """
        Delete the selected execution after explicit confirmation.

        Rechecks ownership and account activity, then delegates
        deletion to the journal service. Invalid historical changes
        are rejected and rolled back by the service.
        """
        if self.m_service is None:
            return

        execution_id = self.get_selected_execution_id()

        if execution_id is None:
            return

        execution = self.m_repository.get_execution(execution_id)

        position = self.m_repository.get_position(self.m_position_id)

        # Protect against stale selections and cross-position actions.
        if execution is None or position is None or execution.position_id != self.m_position_id:
            self.refresh_details()
            return

        account = (
            self.m_repository.get_trading_account(position.account_id) if position.account_id is not None else None
        )

        if account is None or not account.is_active:
            QMessageBox.warning(
                self,
                "Trading Account",
                "Archived trading accounts are read-only.",
            )
            self.refresh_details()
            return

        dialog = DeleteExecutionDialog(
            execution=execution,
            ticker=position.ticker,
            parent=self,
        )

        if dialog.exec() != QDialog.Accepted:
            return

        try:
            deleted = self.m_service.delete_execution(execution_id)

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Execution Deletion",
                str(error),
            )
            self.refresh_details()
            return

        if not deleted:
            QMessageBox.warning(
                self,
                "Execution Not Found",
                "The selected execution could not be deleted.",
            )

        self.refresh_details()
