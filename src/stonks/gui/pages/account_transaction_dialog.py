"""Create or edit a journal account cash transaction."""

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Optional

from PySide6.QtCore import QDateTime
from PySide6.QtWidgets import (
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from stonks.journal.models.account_transaction import AccountTransaction
from stonks.journal.models.account_transaction_type import AccountTransactionType


class AccountTransactionDialog(QDialog):
    """Edit deposits, withdrawals, standalone fees, or signed adjustments.

    Attributes:
        m_account_id: Immutable owning account ID.
        m_transaction: Optional persisted record being edited.
        m_type: Non-transfer transaction type selector.
        m_occurred_at: User-local transaction date and time field.
        m_amount: Decimal currency amount entry.
        m_notes: Optional transaction notes entry.
    """

    SUPPORTED_TYPES = (
        AccountTransactionType.DEPOSIT,
        AccountTransactionType.WITHDRAWAL,
        AccountTransactionType.FEE,
        AccountTransactionType.ADJUSTMENT,
    )

    def __init__(
        self,
        account_id: int,
        transaction: Optional[AccountTransaction] = None,
        parent=None,
    ) -> None:
        """Initialize the account transaction form."""
        super().__init__(parent)
        self.m_account_id = account_id
        self.m_transaction = transaction
        self.setWindowTitle("Edit Transaction" if transaction else "New Transaction")
        self.setMinimumWidth(480)
        self._setup_ui()
        if transaction is not None:
            self._populate_fields()

    def _setup_ui(self) -> None:
        """Create validated inputs and modal save/cancel actions."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        title = QLabel("Edit Transaction" if self.m_transaction else "New Transaction")
        title.setObjectName("journalSectionLabel")
        layout.addWidget(title)

        form = QFormLayout()
        self.m_type = QComboBox()
        for kind in self.SUPPORTED_TYPES:
            self.m_type.addItem(kind.value.replace("_", " ").title(), userData=kind.value)
        form.addRow("Type", self.m_type)

        self.m_occurred_at = QDateTimeEdit()
        self.m_occurred_at.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.m_occurred_at.setCalendarPopup(True)
        self.m_occurred_at.setDateTime(QDateTime.currentDateTime())
        form.addRow("Date / Time (Local)", self.m_occurred_at)

        self.m_amount = QLineEdit()
        self.m_amount.setPlaceholderText("e.g. 500.00")
        form.addRow("Amount", self.m_amount)

        self.m_notes = QTextEdit()
        self.m_notes.setPlaceholderText("Optional explanation or account reference...")
        self.m_notes.setFixedHeight(90)
        form.addRow("Notes", self.m_notes)
        layout.addLayout(form)

        helper = QLabel(
            "Enter positive amounts for deposits, withdrawals, and fees. "
            "Adjustments may be positive or negative. Transfers between "
            "tracked accounts will have their own workflow."
        )
        helper.setObjectName("accountMetricsNote")
        helper.setWordWrap(True)
        layout.addWidget(helper)

        footer = QHBoxLayout()
        footer.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        self.m_save_button = QPushButton("Save Changes" if self.m_transaction else "Add Transaction")
        self.m_save_button.clicked.connect(self._validate_and_accept)
        footer.addWidget(cancel)
        footer.addWidget(self.m_save_button)
        layout.addLayout(footer)

    def _populate_fields(self) -> None:
        """Restore existing transaction values for editing."""
        transaction = self.m_transaction
        if transaction is None:
            return
        index = self.m_type.findData(transaction.transaction_type.value)
        if index >= 0:
            self.m_type.setCurrentIndex(index)
        self.m_occurred_at.setDateTime(QDateTime.fromSecsSinceEpoch(int(transaction.occurred_at.timestamp())))
        self.m_amount.setText(str(transaction.amount))
        self.m_notes.setPlainText(transaction.notes)

    def get_transaction(self) -> AccountTransaction:
        """Build a validated entity with its immutable account and record IDs."""
        kind = AccountTransactionType(self.m_type.currentData())
        try:
            amount = Decimal(self.m_amount.text().strip())
        except (ValueError, InvalidOperation):
            raise ValueError("Amount must be a valid decimal number.")
        if not amount.is_finite():
            raise ValueError("Amount must be finite.")
        if kind == AccountTransactionType.ADJUSTMENT:
            if amount == 0:
                raise ValueError("Adjustment must be nonzero.")
        elif amount <= 0:
            raise ValueError("Amount must be greater than zero.")
        occurred_at = datetime.fromtimestamp(self.m_occurred_at.dateTime().toSecsSinceEpoch(), tz=timezone.utc)
        return AccountTransaction(
            transaction_type=kind,
            occurred_at=occurred_at,
            amount=amount,
            transaction_id=(self.m_transaction.transaction_id if self.m_transaction else None),
            account_id=self.m_account_id,
            notes=self.m_notes.toPlainText().strip(),
        )

    def _validate_and_accept(self) -> None:
        """Keep the dialog open when user input is invalid."""
        try:
            self.get_transaction()
        except ValueError as error:
            QMessageBox.warning(self, "Transaction Validation", str(error))
            return
        self.accept()
