# =============================================================================
# File: create_account_dialog.py
# Purpose: Collect user input for creating a trading account.
# =============================================================================

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
    Collect the information needed to create a trading account.

    Attributes:
        m_name:
            Input field for the account name.
        m_account_type:
            Dropdown for the brokerage account classification.
        m_broker:
            Input field for the brokerage name.
    """

    def __init__(self, parent=None) -> None:
        """Initialize the account creation dialog."""
        super().__init__(parent)

        self.setWindowTitle("Create Trading Account")
        self.setMinimumWidth(380)

        self._setup_ui()

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
        Construct a trading account from the entered information.

        Returns:
            TradingAccount:
                New account containing the user's entered values.
        """
        return TradingAccount(
            name=self.m_name.text(),
            account_type=AccountType(self.m_account_type.currentData()),
            broker=self.m_broker.text(),
        )
