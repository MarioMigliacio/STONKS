# =============================================================================
# File: opening_cash_dialog.py
# Purpose: Edit a dated opening cash snapshot for a tracked trading account.
# =============================================================================

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Optional

from PySide6.QtCore import QDateTime
from PySide6.QtWidgets import (
    QDateTimeEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from stonks.journal.models.opening_cash_balance import OpeningCashBalance


class OpeningCashDialog(QDialog):
    """Edit the cash snapshot from which a tracked account ledger begins.

    Attributes:
        m_account_id:
            Immutable identifier of the tracked trading account.

        m_opening:
            Optional existing snapshot for editing.

        m_amount:
            Decimal cash amount entry.

        m_effective_at:
            Local timestamp editor for the snapshot effective instant.

        m_save_button:
            Button that validates and accepts the submitted snapshot.
    """

    def __init__(
        self,
        account_id: int,
        opening: Optional[OpeningCashBalance] = None,
        parent=None,
    ) -> None:
        """Initialize the editor for a single trading account."""
        super().__init__(parent)
        self.m_account_id = account_id
        self.m_opening = opening
        self.setWindowTitle("Edit Opening Cash" if opening else "Set Opening Cash")
        self.setMinimumWidth(480)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        title = QLabel("Opening Cash Balance")
        title.setObjectName("journalSectionLabel")
        layout.addWidget(title)

        form = QFormLayout()
        self.m_amount = QLineEdit()
        self.m_amount.setPlaceholderText("e.g. 2500.00")
        form.addRow("Opening Cash ($)", self.m_amount)

        self.m_effective_at = QDateTimeEdit()
        self.m_effective_at.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.m_effective_at.setCalendarPopup(True)
        self.m_effective_at.setDateTime(QDateTime.currentDateTime())
        form.addRow("Effective Date / Time (Local)", self.m_effective_at)
        layout.addLayout(form)

        hint = QLabel(
            "This amount is a starting cash snapshot, not a deposit or profit. "
            "Transactions and trades before its effective date are not added "
            "again to cash. Changes that invalidate existing transfers are rejected."
        )
        hint.setObjectName("accountMetricsNote")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        footer = QHBoxLayout()
        footer.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        self.m_save_button = QPushButton("Save Opening Cash")
        self.m_save_button.clicked.connect(self._validate_and_accept)
        footer.addWidget(cancel)
        footer.addWidget(self.m_save_button)
        layout.addLayout(footer)

        if opening is not None:
            self.m_amount.setText(str(opening.amount))
            self.m_effective_at.setDateTime(QDateTime.fromSecsSinceEpoch(int(opening.effective_at.timestamp())))

    def get_opening_cash(self) -> OpeningCashBalance:
        """Build the validated opening cash value from user input."""
        try:
            amount = Decimal(self.m_amount.text().strip())
        except (InvalidOperation, ValueError):
            raise ValueError("Opening cash must be a valid decimal amount.") from None

        if not amount.is_finite() or amount < 0:
            raise ValueError("Opening cash must be a finite, non-negative amount.")

        timestamp = datetime.fromtimestamp(self.m_effective_at.dateTime().toSecsSinceEpoch(), tz=timezone.utc)
        return OpeningCashBalance(self.m_account_id, amount, timestamp)

    def _validate_and_accept(self) -> None:
        """Keep the dialog open when opening cash inputs are invalid."""
        try:
            self.get_opening_cash()
        except ValueError as error:
            QMessageBox.warning(self, "Opening Cash Validation", str(error))
            return
        self.accept()
