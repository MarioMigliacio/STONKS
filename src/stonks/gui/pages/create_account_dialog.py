# =============================================================================
# File: create_account_dialog.py
# Purpose: Collect user input for creating a trading account.
# =============================================================================

from typing import Optional

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
)

from stonks.journal.models.account_type import AccountType
from stonks.journal.models.trading_account import TradingAccount


class CreateAccountDialog(QDialog):
    """
    Collect account information for creating or editing a trading account.

    Attributes:
        m_name:
            Input field for the account name.
        m_account_type:
            Dropdown for the brokerage account classification.
        m_broker:
            Input field for the brokerage name.
    """

    def __init__(
        self,
        parent=None,
        account: Optional[TradingAccount] = None,
    ) -> None:
        """Initialize account fields for creation or editing.

        Args:
            parent:
                Optional parent Qt widget.

            account:
                Existing account to edit, or None when creating an account.
        """
        super().__init__(parent)

        self.m_existing_account = account

        self.setWindowTitle("Edit Trading Account" if account else "Create Trading Account")
        self.setMinimumWidth(380)

        self._setup_ui()

        if account is not None:
            self.m_name.setText(account.name)
            self.m_broker.setText(account.broker)

            index = self.m_account_type.findData(account.account_type.value)
            self.m_account_type.setCurrentIndex(index)

    def _setup_ui(self) -> None:
        """Construct account entry fields and dialog controls."""
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.m_name = QLineEdit()
        self.m_name.setPlaceholderText("e.g. Webull Roth IRA")

        self.m_account_type = QComboBox()

        for account_type in AccountType:
            label = account_type.value.replace("_", " ").title()

            self.m_account_type.addItem(
                label,
                userData=account_type.value,
            )

        self.m_broker = QLineEdit()
        self.m_broker.setPlaceholderText("e.g. Webull")

        form.addRow("Account Name:", self.m_name)
        form.addRow("Account Type:", self.m_account_type)
        form.addRow("Broker:", self.m_broker)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def get_account(self) -> TradingAccount:
        """
        Construct a trading account from the dialog fields.

        Returns:
            TradingAccount:
                New or updated account with its identity and state preserved.
        """
        existing = self.m_existing_account

        return TradingAccount(
            name=self.m_name.text(),
            account_type=AccountType(self.m_account_type.currentData()),
            broker=self.m_broker.text(),
            account_id=existing.account_id if existing else None,
            is_active=existing.is_active if existing else True,
            is_default=existing.is_default if existing else False,
        )
