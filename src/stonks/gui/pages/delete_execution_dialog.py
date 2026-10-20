# =============================================================================
# File: delete_execution_dialog.py
# Purpose: Confirms permanent deletion of a trade execution.
# =============================================================================

from datetime import timezone

from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from stonks.gui.icons import get_icon
from stonks.journal.models.trade_execution import TradeExecution


class DeleteExecutionDialog(QDialog):
    """
    Confirm permanent deletion of a journal trade execution.

    Identifies the selected execution and warns that deleting
    historical trades may invalidate the remaining position history.
    Validation and persistence remain the responsibility of the
    journal service.

    Attributes:
        m_execution:
            Trade execution selected for permanent deletion.

        m_ticker:
            Ticker symbol of the owning journal position.

        m_warning_icon:
            Warning icon indicating an irreversible action.

        m_details_label:
            Label identifying the execution being deleted.

        m_cancel_button:
            Button that dismisses the dialog without deleting.

        m_delete_button:
            Danger-styled button that confirms deletion.
    """

    def __init__(
        self,
        execution: TradeExecution,
        ticker: str,
        parent=None,
    ) -> None:
        """
        Initialize the execution deletion confirmation.

        Args:
            execution:
                Existing execution selected for deletion.

            ticker:
                Ticker symbol of the owning position.

            parent:
                Optional parent Qt widget.
        """
        super().__init__(parent)

        self.m_execution = execution
        self.m_ticker = ticker

        self.setWindowTitle("Delete Trade Execution")
        self.setMinimumWidth(440)
        self.setModal(True)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Construct the execution deletion confirmation interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # Warning heading.
        heading_layout = QHBoxLayout()

        self.m_warning_icon = QLabel()
        self.m_warning_icon.setPixmap(get_icon("triangle-alert").pixmap(QSize(32, 32)))

        heading = QLabel("Delete Trade Execution?")
        heading.setObjectName("dangerHeading")

        heading_layout.addWidget(self.m_warning_icon)
        heading_layout.addWidget(heading)
        heading_layout.addStretch()

        layout.addLayout(heading_layout)

        description = QLabel("You are about to permanently delete the following trade execution.")
        description.setWordWrap(True)
        layout.addWidget(description)

        # Execution details.
        execution = self.m_execution

        executed_at_utc = execution.executed_at.astimezone(timezone.utc)

        self.m_details_label = QLabel(
            f"Ticker: {self.m_ticker}\n"
            f"Direction: {execution.side.value}\n"
            f"Shares: {execution.shares}\n"
            f"Price: ${execution.price:,.4f}\n"
            f"Executed (UTC): "
            f"{executed_at_utc:%Y-%m-%d %H:%M:%S}\n"
            f"Execution ID: {execution.execution_id}"
        )
        self.m_details_label.setObjectName("deletionSummary")
        layout.addWidget(self.m_details_label)

        # Deletion warning.
        warning = QLabel(
            "This execution and its notes will be permanently removed.\n\n"
            "Deleting an earlier trade can invalidate subsequent "
            "executions. STONKS will reject the deletion if the "
            "remaining position history becomes invalid."
        )
        warning.setWordWrap(True)
        warning.setObjectName("dangerWarning")
        layout.addWidget(warning)

        # Confirmation controls.
        buttons = QHBoxLayout()
        buttons.addStretch()

        self.m_cancel_button = QPushButton("Cancel")

        self.m_delete_button = QPushButton("Delete Execution")
        self.m_delete_button.setObjectName("dangerButton")
        self.m_delete_button.setIcon(get_icon("trash"))

        buttons.addWidget(self.m_cancel_button)
        buttons.addWidget(self.m_delete_button)

        layout.addLayout(buttons)

        self.m_cancel_button.clicked.connect(self.reject)
        self.m_delete_button.clicked.connect(self.accept)

        self.m_cancel_button.setFocus()
