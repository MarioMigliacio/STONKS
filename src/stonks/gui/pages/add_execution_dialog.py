# =============================================================================
# File: add_execution_dialog.py
# Purpose: Collects information for a new BUY or SELL execution.
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

from stonks.gui.icons import get_icon
from stonks.journal.models.execution_side import ExecutionSide
from stonks.journal.models.trade_execution import TradeExecution


class AddExecutionDialog(QDialog):
    """
    Collect details for a filled BUY or SELL trade execution.

    Financial inputs are converted directly from text to Decimal.
    Timestamps are entered in local time and stored in UTC.

    Attributes:
        m_position_id:
            Identifier of the position receiving the execution.

        m_ticker:
            Ticker symbol displayed for context.

        m_side:
            Dropdown selecting BUY or SELL.

        m_executed_at:
            Date and time when the trade was filled.

        m_execution:
            Underlying TradeExecution data.

        m_shares:
            Text input for the executed share quantity.

        m_price:
            Text input for the execution price per share.

        m_fees:
            Text input for commissions or other fees.

        m_notes:
            Optional execution-specific notes.

        m_cancel_button:
            Button that dismisses the dialog.

        m_save_button:
            Button that validates and accepts the entered execution.
    """

    def __init__(
        self,
        position_id: int,
        ticker: str,
        parent=None,
        execution: Optional[TradeExecution] = None,
    ) -> None:
        """
        Initialize the execution creation or editing form.

        Args:
            position_id:
                Identifier of the position owning the execution.

            ticker:
                Ticker symbol displayed for context.

            parent:
                Optional parent Qt widget.

            execution:
                Existing execution to edit, or None when creating.
        """
        super().__init__(parent)

        if execution is not None and execution.position_id != position_id:
            raise ValueError("Execution does not belong to the selected position.")

        self.m_position_id = position_id
        self.m_ticker = ticker
        self.m_execution = execution

        self.setWindowTitle("Edit Trade Execution" if execution is not None else "Add Trade Execution")
        self.setMinimumWidth(440)

        self._setup_ui()

        if self.m_execution is not None:
            self._populate_fields()

    def _setup_ui(self) -> None:
        """Build the execution entry form."""
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        is_editing = self.m_execution is not None

        heading = QLabel(f"{'Edit' if is_editing else 'Add'} Execution — {self.m_ticker}")
        heading.setObjectName("pageTitle")
        layout.addWidget(heading)

        form = QFormLayout()

        self.m_side = QComboBox()
        self.m_side.addItem("BUY", userData=ExecutionSide.BUY)
        self.m_side.addItem("SELL", userData=ExecutionSide.SELL)

        self.m_executed_at = QDateTimeEdit()
        self.m_executed_at.setCalendarPopup(True)
        self.m_executed_at.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.m_executed_at.setDateTime(QDateTime.currentDateTime())

        self.m_shares = QLineEdit()
        self.m_shares.setPlaceholderText("e.g. 10.5")

        self.m_price = QLineEdit()
        self.m_price.setPlaceholderText("e.g. 150.1250")

        self.m_fees = QLineEdit()
        self.m_fees.setText("0.00")

        self.m_notes = QTextEdit()
        self.m_notes.setPlaceholderText("Optional notes about this fill...")
        self.m_notes.setFixedHeight(80)

        form.addRow("Side", self.m_side)
        form.addRow("Fill Time (Local)", self.m_executed_at)
        form.addRow("Shares *", self.m_shares)
        form.addRow("Price / Share *", self.m_price)
        form.addRow("Fees", self.m_fees)
        form.addRow("Notes", self.m_notes)

        layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.addStretch()

        self.m_cancel_button = QPushButton("Cancel")

        self.m_save_button = QPushButton("Add Execution")
        self.m_save_button.setIcon(get_icon("plus"))

        buttons.addWidget(self.m_cancel_button)
        buttons.addWidget(self.m_save_button)

        layout.addLayout(buttons)

        self.m_cancel_button.clicked.connect(self.reject)
        self.m_save_button.clicked.connect(self._validate_and_accept)

        self.m_shares.setFocus()

    @staticmethod
    def _parse_decimal(
        value: str,
        field_name: str,
        allow_zero: bool = False,
    ) -> Decimal:
        """
        Parse and validate a nonnegative decimal input.

        Args:
            value:
                Raw text supplied by the user.

            field_name:
                Name displayed in validation messages.

            allow_zero:
                Whether zero is an acceptable value.

        Returns:
            Decimal:
                Parsed financial or share quantity.

        Raises:
            ValueError:
                If the number is missing, invalid, or outside
                the permitted range.
        """
        try:
            number = Decimal(value.strip())
        except (InvalidOperation, ValueError):
            raise ValueError(f"{field_name} must be a valid decimal number.")

        if not number.is_finite():
            raise ValueError(f"{field_name} must be a finite number.")

        if number < 0 or (number == 0 and not allow_zero):
            condition = "zero or greater" if allow_zero else "greater than zero"
            raise ValueError(f"{field_name} must be {condition}.")

        return number

    def get_execution(self) -> TradeExecution:
        """
        Construct a trade execution from the entered values.

        The Qt date-time editor displays local time. Its epoch
        timestamp is converted to a timezone-aware UTC datetime.

        Returns:
            TradeExecution:
                Unsaved execution with validated numeric inputs.

        Raises:
            ValueError:
                If a required numeric input is invalid.
        """
        shares = self._parse_decimal(
            self.m_shares.text(),
            "Shares",
        )
        price = self._parse_decimal(
            self.m_price.text(),
            "Price",
        )
        fees = self._parse_decimal(
            self.m_fees.text(),
            "Fees",
            allow_zero=True,
        )

        executed_at = datetime.fromtimestamp(
            self.m_executed_at.dateTime().toSecsSinceEpoch(),
            tz=timezone.utc,
        )

        return TradeExecution(
            position_id=self.m_position_id,
            execution_id=(self.m_execution.execution_id if self.m_execution is not None else None),
            side=ExecutionSide(self.m_side.currentText()),
            executed_at=executed_at,
            shares=shares,
            price=price,
            fees=fees,
            notes=self.m_notes.toPlainText().strip(),
        )

    def _validate_and_accept(self) -> None:
        """Validate entry fields before accepting the dialog."""
        try:
            self.get_execution()
        except ValueError as error:
            QMessageBox.warning(
                self,
                "Execution Validation",
                str(error),
            )
            return

        self.accept()

    def _populate_fields(self) -> None:
        """Populate the form with an existing trade execution."""
        execution = self.m_execution

        if execution is None:
            return

        index = self.m_side.findText(execution.side.value)

        if index >= 0:
            self.m_side.setCurrentIndex(index)

        # Stored timestamps are UTC; display them in local time.
        local_datetime = execution.executed_at.astimezone()

        self.m_executed_at.setDateTime(QDateTime.fromSecsSinceEpoch(int(local_datetime.timestamp())))

        self.m_shares.setText(str(execution.shares))
        self.m_price.setText(str(execution.price))
        self.m_fees.setText(str(execution.fees))
        self.m_notes.setPlainText(execution.notes)
