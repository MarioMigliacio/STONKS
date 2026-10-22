# =============================================================================
# File: account_transfer_dialog.py
# Purpose: Create or edit a linked transfer between tracked trading accounts.
# =============================================================================

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

from stonks.journal.models.account_transfer import AccountTransfer
from stonks.journal.persistence.journal_repository import JournalRepository


class AccountTransferDialog(QDialog):
    """Enter a transfer between two tracked accounts without editing its direction.

    Attributes:
        m_repository:
            Repository used to populate the account selectors.

        m_transfer:
            Persisted transfer to edit, or None for a new transfer.

        m_source:
            Source account selector.

        m_destination:
            Destination account selector.

        m_amount:
            Positive, finite Decimal input.

        m_occurred_at:
            Local date and time editor.

        m_notes:
            Optional transfer notes.

        m_save_button:
            Submit button, enabled only when appropriate accounts exist.
    """

    def __init__(
        self,
        repository: JournalRepository,
        current_account_id: int,
        transfer: Optional[AccountTransfer] = None,
        parent=None,
    ) -> None:
        """Build a transfer form for creating or updating an internal transfer.

        Args:
            repository:
                Journal repository providing available trading accounts.

            current_account_id:
                Account used to initialize the selection controls.

            transfer:
                Existing transfer to edit, or None for a new transfer.

            parent:
                Optional parent Qt widget.
        """
        super().__init__(parent)
        self.m_repository = repository
        self.m_transfer = transfer
        self.setWindowTitle("Edit Transfer" if transfer else "Transfer Funds")
        self.setMinimumWidth(490)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        title = QLabel("Edit Transfer" if transfer else "Transfer Funds")
        title.setObjectName("journalSectionLabel")
        layout.addWidget(title)

        form = QFormLayout()
        self.m_source = QComboBox()
        self.m_destination = QComboBox()
        self.m_source.setObjectName("journalAccountSelector")
        self.m_destination.setObjectName("journalAccountSelector")
        for account in repository.get_trading_accounts():
            if account.is_active or (
                transfer is not None
                and account.account_id in (transfer.source_account_id, transfer.destination_account_id)
            ):
                name = account.name + (" (Archived)" if not account.is_active else "")
                self.m_source.addItem(name, userData=account.account_id)
                self.m_destination.addItem(name, userData=account.account_id)
        self.m_source.setCurrentIndex(self.m_source.findData(current_account_id))
        self.m_destination.setCurrentIndex(self.m_destination.findData(current_account_id))
        form.addRow("From Account", self.m_source)
        form.addRow("To Account", self.m_destination)

        self.m_amount = QLineEdit()
        self.m_amount.setPlaceholderText("e.g. 250.00")
        form.addRow("Amount", self.m_amount)

        self.m_occurred_at = QDateTimeEdit()
        self.m_occurred_at.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.m_occurred_at.setCalendarPopup(True)
        self.m_occurred_at.setDateTime(QDateTime.currentDateTime())
        form.addRow("Date / Time (Local)", self.m_occurred_at)

        self.m_notes = QTextEdit()
        self.m_notes.setPlaceholderText("Optional transfer description...")
        self.m_notes.setFixedHeight(90)
        form.addRow("Notes", self.m_notes)
        layout.addLayout(form)

        hint = QLabel(
            "Internal transfers reallocate cash. They do not count as deposits, withdrawals, or trading profit."
        )
        hint.setObjectName("accountMetricsNote")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        footer = QHBoxLayout()
        footer.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        self.m_save_button = QPushButton("Save Changes" if transfer else "Transfer Funds")
        self.m_save_button.clicked.connect(self._validate_and_accept)
        footer.addWidget(cancel)
        footer.addWidget(self.m_save_button)
        layout.addLayout(footer)

        if transfer is not None:
            self.m_source.setCurrentIndex(self.m_source.findData(transfer.source_account_id))
            self.m_destination.setCurrentIndex(self.m_destination.findData(transfer.destination_account_id))
            self.m_source.setEnabled(False)
            self.m_destination.setEnabled(False)
            self.m_amount.setText(str(transfer.amount))
            self.m_occurred_at.setDateTime(QDateTime.fromSecsSinceEpoch(int(transfer.occurred_at.timestamp())))
            self.m_notes.setPlainText(transfer.notes)

        self.m_save_button.setEnabled(self.m_source.count() >= 2 and self.m_destination.count() >= 2)

    def get_transfer(self) -> AccountTransfer:
        """Return validated transfer input with immutable identity on edits."""
        source = self.m_source.currentData()
        destination = self.m_destination.currentData()
        if source is None or destination is None:
            raise ValueError("Select two tracked accounts.")
        if source == destination:
            raise ValueError("Source and destination accounts must differ.")
        try:
            amount = Decimal(self.m_amount.text().strip())
        except (InvalidOperation, ValueError):
            raise ValueError("Amount must be a valid decimal number.") from None
        if not amount.is_finite() or amount <= 0:
            raise ValueError("Transfer amount must be a positive finite Decimal.")
        timestamp = datetime.fromtimestamp(self.m_occurred_at.dateTime().toSecsSinceEpoch(), tz=timezone.utc)
        return AccountTransfer(
            source_account_id=source,
            destination_account_id=destination,
            amount=amount,
            occurred_at=timestamp,
            notes=self.m_notes.toPlainText().strip(),
            transfer_id=(self.m_transfer.transfer_id if self.m_transfer else None),
        )

    def _validate_and_accept(self) -> None:
        """Keep the form open on invalid input."""
        try:
            self.get_transfer()
        except ValueError as error:
            QMessageBox.warning(self, "Transfer Validation", str(error))
            return
        self.accept()
