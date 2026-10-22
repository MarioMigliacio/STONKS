# =============================================================================
# File: delete_account_transaction_dialog.py
# Purpose: Confirm deletion of a single non-trade account transaction.
# =============================================================================

from datetime import timezone

from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from stonks.gui.icons import get_icon
from stonks.journal.models.account_transaction import AccountTransaction


class DeleteAccountTransactionDialog(QDialog):
    """Identify the selected transaction before permanently deleting it.

    Attributes:
        m_transaction: Persisted transaction pending user confirmation.
    """

    def __init__(self, transaction: AccountTransaction, parent=None) -> None:
        """Build the cancellation-first transaction deletion confirmation.

        Args:
            transaction:
                Persisted non-transfer transaction selected for deletion.

            parent:
                Optional parent Qt widget.
        """
        super().__init__(parent)
        self.m_transaction = transaction
        self.setWindowTitle("Delete Account Transaction")
        self.setMinimumWidth(430)
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        title = QLabel("Delete Account Transaction?")
        title.setObjectName("dangerHeading")
        layout.addWidget(title)
        when = transaction.occurred_at.astimezone(timezone.utc)
        summary = QLabel(
            f"Type: {transaction.transaction_type.value.replace('_', ' ').title()}\n"
            f"Amount: {transaction.amount}\n"
            f"Occurred (UTC): {when:%Y-%m-%d %H:%M:%S}\n"
            f"Transaction ID: {transaction.transaction_id}"
        )
        summary.setObjectName("deletionSummary")
        layout.addWidget(summary)
        warning = QLabel(
            "This permanently removes the ledger entry and changes account "
            "balances and contributions. This action cannot be undone."
        )
        warning.setWordWrap(True)
        warning.setObjectName("dangerWarning")
        layout.addWidget(warning)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        delete = QPushButton("Delete Transaction")
        delete.setObjectName("dangerButton")
        delete.setIcon(get_icon("trash"))
        delete.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(delete)
        layout.addLayout(buttons)
        cancel.setFocus()
