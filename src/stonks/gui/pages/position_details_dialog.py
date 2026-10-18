# =============================================================================
# File: position_details_dialog.py
# Purpose: Displays position information and trade execution history.
# =============================================================================

from typing import Optional

from PySide6.QtCore import Qt
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
)

from stonks.gui.icons import get_icon
from stonks.gui.pages.add_execution_dialog import AddExecutionDialog
from stonks.journal.persistence.journal_repository import JournalRepository
from stonks.journal.services.journal_service import JournalService


class PositionDetailsDialog(QDialog):
    """
    Display detailed information about a journal trading position.

    Retrieves persisted position metadata and chronological
    execution history. Archived accounts remain available for
    historical review, but cannot receive new executions.

    Attributes:
        m_position_id:
            Identifier of the position being displayed.

        m_repository:
            Repository providing persisted position and execution data.

        m_service:
            Optional journal service for future execution operations.

        m_title:
            Heading identifying the current trading position.

        m_metadata_label:
            Label displaying the position's strategy and catalyst.

        m_add_execution_button:
            Button reserved for adding BUY or SELL executions.

        m_executions_table:
            Table displaying the position's execution history.

        m_empty_label:
            Informational label shown when no executions exist.

        m_close_button:
            Button that closes the details dialog.
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
                Optional journal service for execution operations.

            parent:
                Optional parent Qt widget.
        """
        super().__init__(parent)

        self.m_position_id = position_id
        self.m_repository = repository
        self.m_service = service

        self.setWindowTitle("Position Details")
        self.resize(900, 550)
        self.setMinimumSize(750, 500)
        self._setup_ui()
        self.refresh_details()

    def _setup_ui(self) -> None:
        """Build the position details interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self.m_title = QLabel("Position Details")
        self.m_title.setObjectName("pageTitle")
        layout.addWidget(self.m_title)

        self.m_metadata_label = QLabel()
        self.m_metadata_label.setWordWrap(True)
        layout.addWidget(self.m_metadata_label)

        header_layout = QHBoxLayout()

        heading = QLabel("Trade Executions")
        heading.setObjectName("pageTitle")

        self.m_add_execution_button = QPushButton("Add Execution")
        self.m_add_execution_button.setIcon(get_icon("plus"))
        self.m_add_execution_button.clicked.connect(self._add_execution)

        # The entry workflow is implemented in C3.4B.
        self.m_add_execution_button.setEnabled(False)

        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.m_add_execution_button)

        layout.addLayout(header_layout)

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

        # Allow users to manually resize individual columns.
        header = self.m_executions_table.horizontalHeader()

        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setMinimumSectionSize(60)

        # Give each column a sensible starting width.
        column_widths = {
            0: 165,  # Date / Time (UTC)
            1: 70,  # Side
            2: 90,  # Shares
            3: 110,  # Price
            4: 90,  # Fees
            5: 120,  # Value
            6: 110,  # Execution ID
        }

        for column, width in column_widths.items():
            self.m_executions_table.setColumnWidth(column, width)

        # Let Qt show a scrollbar instead of squeezing columns.
        self.m_executions_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Use extra available space without sacrificing column widths.
        header.setStretchLastSection(True)

        layout.addWidget(self.m_executions_table)

        self.m_empty_label = QLabel("No trade executions recorded for this position.")
        self.m_empty_label.setObjectName("emptyState")
        layout.addWidget(self.m_empty_label)

        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        self.m_close_button = QPushButton("Close")
        self.m_close_button.clicked.connect(self.accept)

        footer_layout.addWidget(self.m_close_button)
        layout.addLayout(footer_layout)

    def refresh_details(self) -> None:
        """Reload position metadata and chronological execution history."""
        position = self.m_repository.get_position(self.m_position_id)

        if position is None:
            self.m_title.setText("Position Not Found")
            self.m_metadata_label.setText("This position no longer exists.")
            self.m_executions_table.setRowCount(0)
            self.m_empty_label.setVisible(False)
            self.m_add_execution_button.setEnabled(False)
            return

        self.m_title.setText(f"{position.ticker} — Position Details")

        self.m_metadata_label.setText(
            f"Strategy: {position.strategy or '—'}\n"
            f"Catalyst: {position.catalyst or '—'}\n"
            f"Entry Reason: {position.entry_reason or '—'}"
        )

        account = (
            self.m_repository.get_trading_account(position.account_id) if position.account_id is not None else None
        )

        can_add_execution = self.m_service is not None and account is not None and account.is_active

        self.m_add_execution_button.setEnabled(can_add_execution)

        executions = self.m_repository.get_position_executions(self.m_position_id)

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

                if column_index in (2, 3, 4, 5):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

                self.m_executions_table.setItem(
                    row_index,
                    column_index,
                    item,
                )

        self.m_empty_label.setVisible(len(executions) == 0)

    def _add_execution(self) -> None:
        """
        Create a BUY or SELL execution for the current position.

        Rechecks account status immediately before opening the
        form and delegates persistence and trading validation
        to the journal service.
        """
        if self.m_service is None:
            return

        position = self.m_repository.get_position(self.m_position_id)

        if position is None:
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
