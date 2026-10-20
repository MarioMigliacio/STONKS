# =============================================================================
# File: delete_account_dialog.py
# Purpose: Confirm irreversible trading account deletion.
# =============================================================================

from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from stonks.gui.icons import get_icon


class DeleteAccountDialog(QDialog):
    """
    Confirm permanent deletion of a trading account.

    Presents financial record counts and requires an exact
    account-name match before enabling the deletion button.

    Attributes:
        m_account_name:
            Name of the account awaiting deletion.

        m_warning_icon:
            Red warning icon indicating an irreversible action.

        m_confirmation_input:
            Text field requiring the exact account name.

        m_cancel_button:
            Button that closes the dialog without authorization.

        m_delete_button:
            Destructive confirmation button, initially disabled.
    """

    def __init__(
        self,
        account_name: str,
        summary: dict[str, int],
        parent=None,
    ) -> None:
        """Initialize the confirmation dialog."""
        super().__init__(parent)

        self.m_account_name = account_name

        self.setWindowTitle("Delete Trading Account")
        self.setMinimumWidth(440)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # Warning heading.
        heading_layout = QHBoxLayout()

        self.m_warning_icon = QLabel()
        self.m_warning_icon.setPixmap(get_icon("triangle-alert").pixmap(QSize(32, 32)))

        heading = QLabel("Permanently Delete Account?")
        heading.setObjectName("dangerHeading")

        heading_layout.addWidget(self.m_warning_icon)
        heading_layout.addWidget(heading)
        heading_layout.addStretch()

        layout.addLayout(heading_layout)

        description = QLabel(f"Deleting '{account_name}' will permanently remove the following financial records:")
        description.setWordWrap(True)
        layout.addWidget(description)

        # Financial record summary.
        summary_label = QLabel(
            f"Positions: {summary['positions']}\n"
            f"Trade executions: {summary['executions']}\n"
            f"Account transactions: {summary['transactions']}"
        )
        summary_label.setObjectName("deletionSummary")
        layout.addWidget(summary_label)

        warning = QLabel("This action cannot be undone.")
        warning.setObjectName("dangerWarning")
        layout.addWidget(warning)

        instruction = QLabel(f"Type '{account_name}' to confirm:")
        layout.addWidget(instruction)

        self.m_confirmation_input = QLineEdit()
        self.m_confirmation_input.setPlaceholderText("Enter account name")
        layout.addWidget(self.m_confirmation_input)

        # Action buttons.
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.m_cancel_button = QPushButton("Cancel")

        self.m_delete_button = QPushButton("Delete Permanently")
        self.m_delete_button.setObjectName("dangerButton")
        self.m_delete_button.setIcon(get_icon("trash"))
        self.m_delete_button.setEnabled(False)

        button_layout.addWidget(self.m_cancel_button)
        button_layout.addWidget(self.m_delete_button)

        layout.addLayout(button_layout)

        # Signals.
        self.m_confirmation_input.textChanged.connect(self._update_delete_state)
        self.m_cancel_button.clicked.connect(self.reject)
        self.m_delete_button.clicked.connect(self.accept)

    def _update_delete_state(self, text: str) -> None:
        """
        Enable deletion only when the exact account name is entered.

        Args:
            text:
                Current confirmation text.
        """
        self.m_delete_button.setEnabled(text == self.m_account_name)
