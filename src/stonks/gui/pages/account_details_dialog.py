"""Account-level financial overview and journal transaction management."""

from datetime import timezone
from decimal import Decimal
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from stonks.gui.icons import get_icon
from stonks.gui.pages.account_transaction_dialog import AccountTransactionDialog
from stonks.gui.pages.delete_account_transaction_dialog import DeleteAccountTransactionDialog
from stonks.gui.widgets.account_metrics_widget import AccountMetricsWidget
from stonks.journal.analytics.account_analytics import calculate_account_metrics
from stonks.journal.analytics.position_analytics import calculate_position_metrics
from stonks.journal.models.account_transaction_type import AccountTransactionType
from stonks.journal.persistence.journal_repository import JournalRepository
from stonks.journal.services.journal_service import JournalService


class AccountDetailsDialog(QDialog):
    """Show account metrics, searchable transaction history, and ledger CRUD.

    Attributes:
        m_account_id: Immutable account being inspected.
        m_repository: Source of accounts, positions, and transaction history.
        m_service: Optional validator/persistence service.
        m_title: Trading account name heading.
        m_metadata: Account type, broker, and activity state.
        m_metrics: Reusable financial metric card grid.
        m_add_button: Opens the new-transaction dialog.
        m_actions_button: Contains edit and deletion actions.
        m_search_input: Case-insensitive search over type and notes.
        m_type_filter: Type-specific transaction filter.
        m_table: Persisted account transaction history table.
        m_empty_label: No-data/no-match message.
    """

    def __init__(
        self,
        account_id: int,
        repository: JournalRepository,
        service: Optional[JournalService] = None,
        parent=None,
    ) -> None:
        """Create account details using the established position-dialog layout."""
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
        self.m_actions_button = QPushButton("Actions")
        self.m_menu = QMenu(self)
        self.m_edit_action = self.m_menu.addAction("Edit Transaction")
        self.m_edit_action.setIcon(get_icon("pencil"))
        self.m_menu.addSeparator()
        self.m_delete_action = self.m_menu.addAction("Delete Transaction")
        self.m_delete_action.setIcon(get_icon("trash-danger"))
        self.m_actions_button.setMenu(self.m_menu)
        self.m_edit_action.triggered.connect(self._edit_transaction)
        self.m_delete_action.triggered.connect(self._delete_transaction)
        header.addWidget(self.m_actions_button)
        layout.addLayout(header)

        filters = QHBoxLayout()
        filters.setSpacing(10)
        self.m_search_input = QLineEdit()
        self.m_search_input.setObjectName("journalSearchInput")
        self.m_search_input.setPlaceholderText("Search transactions or notes...")
        self.m_search_input.setClearButtonEnabled(True)
        self.m_search_input.setAccessibleName("Search transactions")
        self.m_search_input.setMinimumHeight(42)
        self.m_type_filter = QComboBox()
        self.m_type_filter.setObjectName("journalStatusFilter")
        self.m_type_filter.setMinimumHeight(42)
        self.m_type_filter.setMinimumWidth(160)
        self.m_type_filter.addItem("All Types", userData=None)
        for kind in AccountTransactionType:
            self.m_type_filter.addItem(kind.value.replace("_", " ").title(), userData=kind.value)
        filters.addWidget(self.m_search_input, 1)
        filters.addWidget(self.m_type_filter)
        layout.addLayout(filters)

        self.m_table = QTableWidget()
        self.m_table.setObjectName("journalPositionsTable")
        self.m_table.setColumnCount(5)
        self.m_table.setHorizontalHeaderLabels(["Date / Time (UTC)", "Type", "Amount", "Notes", "Transaction ID"])
        self.m_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.m_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.m_table.setSelectionMode(QAbstractItemView.SingleSelection)
        header_view = self.m_table.horizontalHeader()
        header_view.setSectionResizeMode(QHeaderView.Interactive)
        header_view.setMinimumSectionSize(70)
        for index, width in enumerate((175, 135, 125, 265, 115)):
            self.m_table.setColumnWidth(index, width)
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

        self.m_search_input.textChanged.connect(self._apply_filters)
        self.m_type_filter.currentIndexChanged.connect(self._apply_filters)
        self.m_table.itemSelectionChanged.connect(self._update_action_state)
        self.m_table.itemDoubleClicked.connect(self._edit_transaction)

    def get_selected_transaction_id(self) -> Optional[int]:
        """Return the persistent identifier for the selected ledger entry."""
        rows = self.m_table.selectionModel().selectedRows()
        if not rows:
            return None
        item = self.m_table.item(rows[0].row(), 0)
        if item is None:
            return None
        result = item.data(Qt.UserRole)
        return result if type(result) is int else None

    def _account_is_active(self) -> bool:
        """Check whether writes are allowed to this trading account."""
        account = self.m_repository.get_trading_account(self.m_account_id)
        return self.m_service is not None and account is not None and account.is_active

    def _update_action_state(self) -> None:
        """Disable edit/delete for missing or archived accounts and hidden rows."""
        transaction_id = self.get_selected_transaction_id()
        transaction = self.m_repository.get_account_transaction(transaction_id) if transaction_id is not None else None
        can_edit = (
            self._account_is_active()
            and transaction is not None
            and transaction.account_id == self.m_account_id
            and transaction.transaction_type in AccountTransactionDialog.SUPPORTED_TYPES
        )
        self.m_edit_action.setEnabled(can_edit)
        self.m_delete_action.setEnabled(can_edit)
        self.m_actions_button.setEnabled(can_edit)

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
        self.m_metrics.show()

        transactions = self.m_repository.get_account_transactions(account_id=self.m_account_id)
        positions = self.m_repository.get_positions(account_id=self.m_account_id)
        executions = []
        position_metrics = []
        for position in positions:
            fills = self.m_repository.get_position_executions(position.position_id)
            executions.extend(fills)
            position_metrics.append(calculate_position_metrics(position.position_id, fills))
        metrics = calculate_account_metrics(transactions, executions, position_metrics)
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

    def _apply_filters(self, *_args) -> None:
        """Apply combined type and text filters to the selected account."""
        needle = self.m_search_input.text().strip().casefold()
        kind = self.m_type_filter.currentData()
        visible = 0
        selected_id = self.get_selected_transaction_id()
        selected_visible = False
        for row in range(self.m_table.rowCount()):
            type_item = self.m_table.item(row, 1)
            note_item = self.m_table.item(row, 3)
            if type_item is None or note_item is None:
                self.m_table.setRowHidden(row, True)
                continue
            type_text = type_item.text()
            record_kind = type_text.replace(" ", "_").upper()
            matches = (not needle or needle in type_text.casefold() or needle in note_item.text().casefold()) and (
                kind is None or kind == record_kind
            )
            self.m_table.setRowHidden(row, not matches)
            if matches:
                visible += 1
                if self.m_table.item(row, 0).data(Qt.UserRole) == selected_id:
                    selected_visible = True
        if not selected_visible:
            self.m_table.clearSelection()
        total = self.m_table.rowCount()
        self.m_empty_label.setText(
            "No account transactions recorded yet."
            if total == 0
            else "No transactions match your current search or filters."
        )
        self.m_empty_label.setVisible(total == 0 or visible == 0)
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
        dialog = AccountTransactionDialog(self.m_account_id, transaction=transaction, parent=self)
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
