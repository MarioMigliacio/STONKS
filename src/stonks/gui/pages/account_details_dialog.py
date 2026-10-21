# =============================================================================
# File: account_details_dialog.py
# Purpose: Account-level financial overview and journal transaction management.
# =============================================================================

from datetime import date, timedelta, timezone
from decimal import Decimal
from typing import Optional

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCalendarWidget,
    QComboBox,
    QDateEdit,
    QDialog,
    QFrame,
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
from stonks.gui.pages.account_transaction_dialog import AccountTransactionDialog
from stonks.gui.pages.account_transfer_dialog import AccountTransferDialog
from stonks.gui.pages.delete_account_transaction_dialog import DeleteAccountTransactionDialog
from stonks.gui.widgets.account_metrics_widget import AccountMetricsWidget
from stonks.journal.analytics.account_analytics import calculate_account_metrics
from stonks.journal.analytics.position_analytics import calculate_position_metrics
from stonks.journal.models.account_transaction_type import AccountTransactionType
from stonks.journal.models.account_transfer import AccountTransfer
from stonks.journal.persistence.journal_repository import JournalRepository
from stonks.journal.services.journal_service import JournalService


class AccountDetailsDialog(QDialog):
    """Display account metrics, date-filtered history, and ledger transactions.

    Attributes:
        m_account_id:
            Identifier of the trading account being inspected.

        m_repository:
            Repository used to retrieve accounts, positions, and transactions.

        m_service:
            Optional journal service for validated transaction writes.

        m_title:
            Label displaying the selected account name.

        m_metadata:
            Account type, broker, and active or archived state.

        m_metrics:
            Reusable account financial metrics widget.

        m_add_button:
            Button opening the transaction creation dialog.

        m_actions_button:
            Button opening the transaction management menu.

        m_menu:
            Menu containing edit and delete actions.

        m_edit_action:
            Action for editing the selected transaction.

        m_delete_action:
            Action for deleting the selected transaction.

        m_type_filter:
            Filter for transaction type.

        m_date_preset:
            Preset for the history date range.

        m_start_date:
            Inclusive start of the custom date range.

        m_end_date:
            Inclusive end of the custom date range.

        m_clear_filters_button:
            Link-style button restoring the default filters.

        m_results_label:
            Count of visible transactions after filtering.

        m_table:
            Persisted account transaction history table.

        m_empty_label:
            Message for empty history, no matches, or an invalid range.
    """

    def __init__(
        self,
        account_id: int,
        repository: JournalRepository,
        service: Optional[JournalService] = None,
        parent=None,
    ) -> None:
        """Initialize a trading account detail and transaction history dialog.

        Args:
            account_id:
                Identifier of the selected trading account.
            repository:
                Journal repository used for retrieving persisted records.
            service:
                Optional service for validated transaction operations.
            parent:
                Optional parent Qt widget.
        """
        super().__init__(parent)

        self.m_account_id = account_id
        self.m_repository = repository
        self.m_service = service

        self.setWindowTitle("Account Details")
        self.resize(900, 800)
        self.setMinimumSize(750, 500)

        self._setup_ui()
        self.refresh_details()

    def _setup_ui(self) -> None:
        """Build the metric cards, filter toolbar, ledger grid, and actions."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self.m_title = QLabel("Account Details")
        self.m_title.setObjectName("journalPageTitle")
        self.m_metadata = QLabel()
        self.m_metadata.setObjectName("journalPageSubtitle")
        self.m_metadata.setWordWrap(True)
        layout.addWidget(self.m_title)
        layout.addWidget(self.m_metadata)

        self.m_metrics = AccountMetricsWidget(self)
        layout.addWidget(self.m_metrics)

        header = QHBoxLayout()
        heading = QLabel("Transaction History")
        heading.setObjectName("metricsHeading")

        header.addWidget(heading)
        header.addStretch()
        self.m_add_button = QPushButton("New Transaction")
        self.m_add_button.setIcon(get_icon("plus"))
        self.m_add_button.clicked.connect(self._create_transaction)

        header.addWidget(self.m_add_button)
        self.m_transfer_button = QPushButton("Transfer Funds")
        self.m_transfer_button.setIcon(get_icon("plus"))
        self.m_transfer_button.clicked.connect(self._create_transfer)
        header.addWidget(self.m_transfer_button)
        self.m_actions_button = QPushButton("Actions")
        self.m_menu = QMenu(self)
        self.m_edit_action = self.m_menu.addAction("Edit Transaction")
        self.m_edit_action.setIcon(get_icon("pencil"))
        self.m_menu.addSeparator()
        self.m_delete_action = self.m_menu.addAction("Delete Transaction")
        self.m_delete_action.setIcon(get_icon("trash-danger"))
        self.m_menu.addSeparator()
        self.m_edit_transfer_action = self.m_menu.addAction("Edit Transfer")
        self.m_edit_transfer_action.setIcon(get_icon("pencil"))
        self.m_delete_transfer_action = self.m_menu.addAction("Delete Transfer")
        self.m_delete_transfer_action.setIcon(get_icon("trash-danger"))
        self.m_actions_button.setMenu(self.m_menu)
        self.m_edit_transfer_action.triggered.connect(self._edit_transfer)
        self.m_delete_transfer_action.triggered.connect(self._delete_transfer)

        self.m_edit_action.triggered.connect(self._edit_transaction)
        self.m_delete_action.triggered.connect(self._delete_transaction)
        header.addWidget(self.m_actions_button)
        layout.addLayout(header)

        # Transaction type and date-preset filters.
        filters = QHBoxLayout()
        filters.setSpacing(10)
        self.m_type_filter = QComboBox()
        self.m_type_filter.setObjectName("journalStatusFilter")
        self.m_type_filter.setMinimumHeight(42)
        self.m_type_filter.setMinimumWidth(160)
        self.m_type_filter.addItem("All Types", userData=None)
        for kind in AccountTransactionType:
            label = kind.value.replace("_", " ").title()
            self.m_type_filter.addItem(label, userData=kind.value)

        self.m_date_preset = QComboBox()
        self.m_date_preset.setObjectName("journalStatusFilter")
        self.m_date_preset.setMinimumHeight(42)
        self.m_date_preset.setMinimumWidth(155)

        for label, key in (
            ("All Time", "all"),
            ("Last 7 Days", "7"),
            ("Last 30 Days", "30"),
            ("Last 90 Days", "90"),
            ("This Year", "year"),
            ("Custom Range", "custom"),
        ):
            self.m_date_preset.addItem(label, userData=key)

        filters.addWidget(self.m_type_filter)
        filters.addWidget(self.m_date_preset)
        filters.addStretch()
        layout.addLayout(filters)

        # Inclusive custom date range; labels are above the inputs.
        date_range = QHBoxLayout()
        date_range.setSpacing(10)
        start_label = QLabel("From")
        start_label.setObjectName("journalAccountLabel")
        self.m_start_date = QDateEdit()
        self.m_start_date.setObjectName("journalDateFilter")
        self.m_start_date.setCalendarPopup(True)
        self.m_start_date.setDisplayFormat("yyyy-MM-dd")
        self.m_start_date.setDate(QDate.currentDate().addDays(-29))
        self.m_start_date.setEnabled(False)
        self._configure_date_editor(self.m_start_date)
        end_label = QLabel("To")
        end_label.setObjectName("journalAccountLabel")
        self.m_end_date = QDateEdit()
        self.m_end_date.setObjectName("journalDateFilter")
        self.m_end_date.setCalendarPopup(True)
        self.m_end_date.setDisplayFormat("yyyy-MM-dd")
        self.m_end_date.setDate(QDate.currentDate())
        self.m_end_date.setEnabled(False)
        self._configure_date_editor(self.m_end_date)

        start_column = QVBoxLayout()
        start_column.setSpacing(6)
        start_column.addWidget(start_label)
        start_column.addWidget(self.m_start_date)

        end_column = QVBoxLayout()
        end_column.setSpacing(6)
        end_column.addWidget(end_label)
        end_column.addWidget(self.m_end_date)

        date_range.addLayout(start_column)
        date_range.addLayout(end_column)
        date_range.addStretch()
        layout.addLayout(date_range)

        separator = QFrame(self)
        separator.setObjectName("accountFilterSeparator")
        separator.setFrameShape(QFrame.HLine)
        separator.setFixedHeight(1)
        layout.addWidget(separator)

        # History count and reset action.
        filter_footer = QHBoxLayout()
        self.m_results_label = QLabel("Showing 0 transactions")
        self.m_results_label.setObjectName("journalPageSubtitle")
        self.m_clear_filters_button = QPushButton("Clear Filters")
        self.m_clear_filters_button.setObjectName("accountClearFiltersLink")
        self.m_clear_filters_button.setCursor(Qt.PointingHandCursor)
        self.m_clear_filters_button.setFlat(True)
        self.m_clear_filters_button.clicked.connect(self._clear_filters)
        filter_footer.addWidget(self.m_results_label)
        filter_footer.addStretch()
        filter_footer.addWidget(self.m_clear_filters_button)
        layout.addLayout(filter_footer)

        self.m_date_preset.currentIndexChanged.connect(self._on_date_preset_changed)
        self.m_start_date.dateChanged.connect(self._apply_filters)
        self.m_end_date.dateChanged.connect(self._apply_filters)
        # Read-only chronological ledger.
        self.m_table = QTableWidget()
        self.m_table.setObjectName("journalPositionsTable")
        self.m_table.setColumnCount(5)
        self.m_table.setHorizontalHeaderLabels(
            [
                "Date / Time (UTC)",
                "Type",
                "Amount",
                "Notes",
                "Transaction ID",
            ]
        )
        self.m_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.m_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.m_table.setSelectionMode(QAbstractItemView.SingleSelection)
        header_view = self.m_table.horizontalHeader()
        header_view.setSectionResizeMode(QHeaderView.Interactive)
        header_view.setMinimumSectionSize(70)
        for index, width in enumerate((175, 135, 125, 265, 115)):
            self.m_table.setColumnWidth(index, width)

        # Stretch the Notes column to fill unused horizontal space.
        header_view.setSectionResizeMode(3, QHeaderView.Stretch)

        self.m_table.verticalHeader().setVisible(False)
        self.m_table.verticalHeader().setDefaultSectionSize(40)
        layout.addWidget(self.m_table)

        self.m_empty_label = QLabel("No account transactions recorded yet.")
        self.m_empty_label.setObjectName("emptyState")
        layout.addWidget(self.m_empty_label)
        footer = QHBoxLayout()
        footer.addStretch()
        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        footer.addWidget(close)
        layout.addLayout(footer)

        self.m_type_filter.currentIndexChanged.connect(self._apply_filters)
        self.m_table.itemSelectionChanged.connect(self._update_action_state)
        self.m_table.itemDoubleClicked.connect(self._edit_selected_entry)

    @staticmethod
    def _configure_date_editor(editor: QDateEdit) -> None:
        """Configure a date field and its popup without embedding visual styles.

        All colors, borders, focus states, and calendar SVG styling are
        defined centrally in ``stonks.gui.styles.theme``.

        Args:
            editor:
                Date editor used for an inclusive history filter.
        """
        editor.setMinimumHeight(42)
        editor.setMinimumWidth(155)
        editor.setCursor(Qt.PointingHandCursor)

        calendar = editor.calendarWidget()
        calendar.setObjectName("accountDateCalendar")
        calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        calendar.setGridVisible(False)

    def get_selected_transaction_id(self) -> Optional[int]:
        """Return the persistent identifier for the selected ledger entry."""
        rows = self.m_table.selectionModel().selectedRows()

        if not rows:
            return None

        item = self.m_table.item(rows[0].row(), 0)

        if item is None:
            return None

        transaction_id = item.data(Qt.UserRole)
        return transaction_id if type(transaction_id) is int else None

    def _account_is_active(self) -> bool:
        """Check whether writes are allowed to this trading account."""
        account = self.m_repository.get_trading_account(self.m_account_id)
        return self.m_service is not None and account is not None and account.is_active

    def _update_action_state(self) -> None:
        """Enable actions appropriate to the selected ledger entry."""
        transaction = self._get_selected_transaction()
        active = self._account_is_active()
        is_transfer = transaction is not None and transaction.transfer_id is not None
        is_regular = (
            transaction is not None and transaction.transaction_type in AccountTransactionDialog.SUPPORTED_TYPES
        )
        self.m_edit_action.setEnabled(active and is_regular)
        self.m_delete_action.setEnabled(active and is_regular)
        self.m_edit_transfer_action.setEnabled(active and is_transfer)
        self.m_delete_transfer_action.setEnabled(active and is_transfer)
        self.m_actions_button.setEnabled(active and (is_regular or is_transfer))

    @staticmethod
    def _format_flow(value: Decimal) -> str:
        """Format signed ledger cash flow without losing the original type."""
        if value > 0:
            return f"+${value:,.2f}"
        if value < 0:
            return f"-${abs(value):,.2f}"
        return "$0.00"

    def refresh_details(self) -> None:
        """Refresh account metadata, backend analytics, and transaction history."""
        selected_id = self.get_selected_transaction_id()
        account = self.m_repository.get_trading_account(self.m_account_id)
        if account is None:
            self.m_title.setText("Account Not Found")
            self.m_metadata.setText("This trading account no longer exists.")
            self.m_table.setRowCount(0)
            self.m_add_button.setEnabled(False)
            self.m_transfer_button.setEnabled(False)
            self.m_empty_label.hide()
            self.m_metrics.hide()
            self._update_action_state()
            return

        self.m_title.setText(account.name)
        state = "Active" if account.is_active else "Archived — Read Only"
        self.m_metadata.setText(
            f"{account.account_type.value.replace('_', ' ').title()}"
            f"  ·  {account.broker or 'Broker not specified'}  ·  {state}"
        )
        self.m_add_button.setEnabled(self._account_is_active())
        self.m_transfer_button.setEnabled(
            self._account_is_active()
            and sum(account.is_active for account in self.m_repository.get_trading_accounts()) >= 2
        )
        self.m_metrics.show()

        transactions = self.m_repository.get_account_transactions(account_id=self.m_account_id)
        positions = self.m_repository.get_positions(account_id=self.m_account_id)

        executions = []
        position_metrics = []

        for position in positions:
            fills = self.m_repository.get_position_executions(position.position_id)
            executions.extend(fills)
            position_metrics.append(calculate_position_metrics(position.position_id, fills))

        metrics = calculate_account_metrics(
            transactions,
            executions,
            position_metrics,
        )
        self.m_metrics.update_metrics(metrics)

        self.m_table.blockSignals(True)
        try:
            self.m_table.clearSelection()
            self.m_table.setRowCount(0)
            self.m_table.setRowCount(len(transactions))
            for row, transaction in enumerate(transactions):
                when = transaction.occurred_at.astimezone(timezone.utc)
                values = (
                    when.strftime("%Y-%m-%d %H:%M:%S"),
                    transaction.transaction_type.value.replace("_", " ").title(),
                    self._format_flow(transaction.net_cash_flow),
                    transaction.notes,
                    str(transaction.transaction_id),
                )
                for column, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setData(Qt.UserRole, transaction.transaction_id)
                    if column == 2:
                        flow = transaction.net_cash_flow
                        if flow > 0:
                            item.setForeground(QColor("#4ADE80"))
                        elif flow < 0:
                            item.setForeground(QColor("#F87171"))
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.m_table.setItem(row, column, item)
            if selected_id is not None:
                for row in range(self.m_table.rowCount()):
                    item = self.m_table.item(row, 0)
                    if item is not None and item.data(Qt.UserRole) == selected_id:
                        self.m_table.selectRow(row)
                        break
        finally:
            self.m_table.blockSignals(False)
        self._apply_filters()

    def _on_date_preset_changed(self, *_args) -> None:
        """Enable date editors only for custom ranges and refresh the ledger."""
        custom = self.m_date_preset.currentData() == "custom"
        self.m_start_date.setEnabled(custom)
        self.m_end_date.setEnabled(custom)
        self._apply_filters()

    def _clear_filters(self) -> None:
        """Return the ledger to its complete, unfiltered account history."""
        self.m_type_filter.setCurrentIndex(0)
        self.m_date_preset.setCurrentIndex(0)
        self._apply_filters()

    def _selected_date_range(self):
        """Return inclusive UTC calendar dates, or None for all-time history."""
        preset = self.m_date_preset.currentData()
        today = date.today()
        if preset == "all":
            return None
        if preset == "custom":
            return (
                self.m_start_date.date().toPython(),
                self.m_end_date.date().toPython(),
            )
        if preset == "year":
            return date(today.year, 1, 1), today
        days = int(preset)
        return today - timedelta(days=days - 1), today

    def _apply_filters(self, *_args) -> None:
        """Filter displayed UTC transaction dates and types, without changing metrics."""
        kind = self.m_type_filter.currentData()
        date_range = self._selected_date_range()
        invalid_range = date_range is not None and date_range[0] > date_range[1]
        visible = 0
        selected_id = self.get_selected_transaction_id()
        selected_visible = False
        for row in range(self.m_table.rowCount()):
            date_item = self.m_table.item(row, 0)
            type_item = self.m_table.item(row, 1)
            if date_item is None or type_item is None:
                self.m_table.setRowHidden(row, True)
                continue
            record_kind = type_item.text().replace(" ", "_").upper()
            record_date = date.fromisoformat(date_item.text()[:10])
            matches_type = kind is None or kind == record_kind
            matches_date = date_range is None or (not invalid_range and date_range[0] <= record_date <= date_range[1])
            matches = matches_type and matches_date
            self.m_table.setRowHidden(row, not matches)
            if matches:
                visible += 1
                if date_item.data(Qt.UserRole) == selected_id:
                    selected_visible = True
        if not selected_visible:
            self.m_table.clearSelection()
        total = self.m_table.rowCount()
        self.m_results_label.setText(f"Showing {visible} of {total} transactions")
        if invalid_range:
            message = "Start date must not be after end date."
        elif total == 0:
            message = "No account transactions recorded yet."
        else:
            message = "No transactions match your current filters."
        self.m_empty_label.setText(message)
        self.m_empty_label.setVisible(invalid_range or total == 0 or visible == 0)
        self._update_action_state()

    def _get_selected_transaction(self):
        """Retrieve a selected record only when owned by the displayed account."""
        record_id = self.get_selected_transaction_id()
        if record_id is None:
            return None
        transaction = self.m_repository.get_account_transaction(record_id)
        if transaction is None or transaction.account_id != self.m_account_id:
            return None
        return transaction

    def _create_transaction(self) -> None:
        """Create a validated non-transfer cash movement in the active account."""
        if not self._account_is_active():
            return
        dialog = AccountTransactionDialog(self.m_account_id, parent=self)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            self.m_service.create_account_transaction(dialog.get_transaction())
        except (ValueError, RuntimeError) as error:
            QMessageBox.warning(self, "Transaction Validation", str(error))
            return
        self.refresh_details()

    def _edit_transaction(self, *_args) -> None:
        """Edit only current-account supported transaction types."""
        if not self._account_is_active():
            return
        transaction = self._get_selected_transaction()
        if transaction is None or transaction.transaction_type not in AccountTransactionDialog.SUPPORTED_TYPES:
            return
        dialog = AccountTransactionDialog(
            self.m_account_id,
            transaction=transaction,
            parent=self,
        )
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            updated = self.m_service.update_account_transaction(dialog.get_transaction())
        except (ValueError, RuntimeError) as error:
            QMessageBox.warning(self, "Transaction Validation", str(error))
            return
        if not updated:
            QMessageBox.warning(self, "Transaction Not Found", "The selected transaction no longer exists.")
        self.refresh_details()

    def _delete_transaction(self) -> None:
        """Delete a selected record after explicit confirmation."""
        if not self._account_is_active():
            return
        transaction = self._get_selected_transaction()
        if transaction is None or transaction.transaction_type not in AccountTransactionDialog.SUPPORTED_TYPES:
            return
        dialog = DeleteAccountTransactionDialog(transaction, parent=self)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            deleted = self.m_service.delete_account_transaction(transaction.transaction_id)
        except (ValueError, RuntimeError) as error:
            QMessageBox.warning(self, "Transaction Deletion", str(error))
            return
        if not deleted:
            QMessageBox.warning(self, "Transaction Not Found", "The selected transaction no longer exists.")
        self.refresh_details()

    def _selected_transfer(self) -> Optional[AccountTransfer]:
        """Resolve a selected transfer from its persisted parent and paired legs."""
        transaction = self._get_selected_transaction()
        if transaction is None or transaction.transfer_id is None:
            return None
        row = self.m_repository.m_connection.execute(
            "SELECT * FROM account_transfers WHERE transfer_id = ?",
            (transaction.transfer_id,),
        ).fetchone()
        if row is None:
            return None
        from datetime import datetime

        return AccountTransfer(
            source_account_id=row["source_account_id"],
            destination_account_id=row["destination_account_id"],
            amount=Decimal(row["amount"]),
            occurred_at=datetime.fromisoformat(row["occurred_at"]),
            notes=row["notes"],
            transfer_id=row["transfer_id"],
        )

    def _create_transfer(self) -> None:
        """Open a form and atomically create both legs of an internal transfer."""
        if not self._account_is_active():
            return
        dialog = AccountTransferDialog(self.m_repository, self.m_account_id, parent=self)
        if dialog.exec() != QDialog.Accepted:
            return
        transfer = dialog.get_transfer()
        try:
            self.m_service.create_account_transfer(
                transfer.source_account_id,
                transfer.destination_account_id,
                transfer.amount,
                transfer.occurred_at,
                transfer.notes,
            )
        except (ValueError, RuntimeError) as error:
            QMessageBox.warning(self, "Transfer Validation", str(error))
            return
        self.refresh_details()

    def _edit_selected_entry(self, *_args) -> None:
        """Route a double-click to the matching editor."""
        transaction = self._get_selected_transaction()
        if transaction is not None and transaction.transfer_id is not None:
            self._edit_transfer()
        else:
            self._edit_transaction()

    def _edit_transfer(self, *_args) -> None:
        """Update the parent transfer and both legs through the journal service."""
        if not self._account_is_active():
            return
        transfer = self._selected_transfer()
        if transfer is None:
            return
        dialog = AccountTransferDialog(self.m_repository, self.m_account_id, transfer=transfer, parent=self)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            updated = self.m_service.update_account_transfer(dialog.get_transfer())
        except (ValueError, RuntimeError) as error:
            QMessageBox.warning(self, "Transfer Validation", str(error))
            return
        if not updated:
            QMessageBox.warning(self, "Transfer Not Found", "This transfer no longer exists.")
        self.refresh_details()

    def _delete_transfer(self) -> None:
        """Delete a complete transfer only after explicit confirmation."""
        if not self._account_is_active():
            return
        transfer = self._selected_transfer()
        if transfer is None:
            return
        source = self.m_repository.get_trading_account(transfer.source_account_id)
        destination = self.m_repository.get_trading_account(transfer.destination_account_id)
        response = QMessageBox.question(
            self,
            "Delete Transfer",
            (
                f"Permanently delete transfer #{transfer.transfer_id}?\n\n"
                f"{source.name if source else 'Unknown'} → {destination.name if destination else 'Unknown'}\n"
                f"Amount: ${transfer.amount:,.2f}\n\n"
                "Both linked ledger entries will be deleted. This cannot be undone."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if response != QMessageBox.Yes:
            return
        try:
            deleted = self.m_service.delete_account_transfer(transfer.transfer_id)
        except (ValueError, RuntimeError) as error:
            QMessageBox.warning(self, "Transfer Deletion", str(error))
            return
        if not deleted:
            QMessageBox.warning(self, "Transfer Not Found", "This transfer no longer exists.")
        self.refresh_details()
