# =============================================================================
# File: create_position_dialog.py
# Purpose: Collects information for creating and editing journal positions.
# =============================================================================

from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from stonks.gui.icons import get_icon
from stonks.journal.models.position import Position


class CreatePositionDialog(QDialog):
    """
    Collect information for creating or editing a journal position.

    Keeps form presentation separate from persistence and
    returns a Position model to the calling page.

    Attributes:
        m_account_id:
            Database identifier of the selected trading account.

        m_account_name:
            Display name of the account owning the position.

        m_position:
            Existing position being edited, or None when creating.

        m_ticker:
            Input for the stock ticker symbol.

        m_strategy:
            Input for the trading strategy or setup.

        m_catalyst:
            Input for the event motivating the trade.

        m_entry_reason:
            Multiline input describing the reason for entry.

        m_exit_reason:
            Multiline input describing the reason for exit.

        m_mistakes:
            Multiline input documenting mistakes or rule violations.

        m_lessons_learned:
            Multiline input documenting lessons from the trade.

        m_notes:
            Multiline input for additional observations.

        m_cancel_button:
            Button that dismisses the dialog without saving.

        m_create_button:
            Button that accepts the position information.
            Displays Save Changes when editing an existing position.
    """

    def __init__(
        self,
        account_id: int,
        account_name: str,
        parent=None,
        position: Optional[Position] = None,
    ) -> None:
        """
        Initialize the position creation or editing form.

        Args:
            account_id:
                Identifier of the account owning the position.

            account_name:
                Display name of the associated trading account.

            parent:
                Optional parent Qt widget.

            position:
                Optional existing position to populate for editing.
        """
        super().__init__(parent)

        if position is not None and position.account_id != account_id:
            raise ValueError("The position does not belong to the selected trading account.")

        self.m_account_id = account_id
        self.m_account_name = account_name
        self.m_position = position

        self.setWindowTitle("Edit Trading Position" if position is not None else "New Trading Position")
        self.setMinimumWidth(440)

        self._setup_ui()

        if self.m_position is not None:
            self._populate_fields()

    def _setup_ui(self) -> None:
        """Build the position entry and editing interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        is_editing = self.m_position is not None

        # Dialog heading.
        title = QLabel("Edit Trading Position" if is_editing else "New Trading Position")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        account_label = QLabel(f"Trading Account: {self.m_account_name}")
        layout.addWidget(account_label)

        # Position metadata fields.
        form = QFormLayout()

        self.m_ticker = QLineEdit()
        self.m_ticker.setPlaceholderText("e.g. NVDA")
        self.m_ticker.setMaxLength(20)

        self.m_strategy = QLineEdit()
        self.m_strategy.setPlaceholderText("e.g. VWAP Reclaim")

        self.m_catalyst = QLineEdit()
        self.m_catalyst.setPlaceholderText("e.g. Positive earnings guidance")

        self.m_entry_reason = QTextEdit()
        self.m_entry_reason.setPlaceholderText("Why did you enter this trade?")
        self.m_entry_reason.setFixedHeight(75)

        self.m_exit_reason = QTextEdit()
        self.m_exit_reason.setPlaceholderText("Why did you exit this position?")
        self.m_exit_reason.setFixedHeight(65)

        self.m_mistakes = QTextEdit()
        self.m_mistakes.setPlaceholderText("Mistakes or rule violations...")
        self.m_mistakes.setFixedHeight(65)

        self.m_lessons_learned = QTextEdit()
        self.m_lessons_learned.setPlaceholderText("What did you learn from this trade?")
        self.m_lessons_learned.setFixedHeight(65)

        self.m_notes = QTextEdit()
        self.m_notes.setPlaceholderText("Additional observations...")
        self.m_notes.setFixedHeight(65)

        form.addRow("Ticker *", self.m_ticker)
        form.addRow("Strategy", self.m_strategy)
        form.addRow("Catalyst", self.m_catalyst)
        form.addRow("Entry Reason", self.m_entry_reason)
        form.addRow("Exit Reason", self.m_exit_reason)
        form.addRow("Mistakes", self.m_mistakes)
        form.addRow("Lessons Learned", self.m_lessons_learned)
        form.addRow("Notes", self.m_notes)

        # Attach the form to the dialog before changing widget visibility.
        layout.addLayout(form)

        # Review fields are introduced when editing a position.
        for widget in (
            self.m_exit_reason,
            self.m_mistakes,
            self.m_lessons_learned,
        ):
            label = form.labelForField(widget)

            widget.setVisible(is_editing)

            if label is not None:
                label.setVisible(is_editing)

        # Dialog action buttons.
        buttons = QHBoxLayout()
        buttons.addStretch()

        self.m_cancel_button = QPushButton("Cancel")

        self.m_create_button = QPushButton("Save Changes" if is_editing else "Create Position")

        self.m_create_button.setIcon(get_icon("pencil" if is_editing else "plus"))
        self.m_create_button.setEnabled(False)

        buttons.addWidget(self.m_cancel_button)
        buttons.addWidget(self.m_create_button)

        layout.addLayout(buttons)

        # Connect signals.
        self.m_ticker.textChanged.connect(self._update_create_state)
        self.m_cancel_button.clicked.connect(self.reject)
        self.m_create_button.clicked.connect(self.accept)

        self.m_ticker.setFocus()

    def _populate_fields(self) -> None:
        """Populate the form with an existing position's information."""
        position = self.m_position

        if position is None:
            return

        self.m_ticker.setText(position.ticker)
        self.m_strategy.setText(position.strategy)
        self.m_catalyst.setText(position.catalyst)

        self.m_entry_reason.setPlainText(position.entry_reason)
        self.m_exit_reason.setPlainText(position.exit_reason)
        self.m_mistakes.setPlainText(position.mistakes)
        self.m_lessons_learned.setPlainText(position.lessons_learned)
        self.m_notes.setPlainText(position.notes)

    def _update_create_state(self, text: str) -> None:
        """
        Enable saving when a nonempty ticker has been entered.

        Args:
            text:
                Current ticker field contents.
        """
        self.m_create_button.setEnabled(bool(text.strip()))

    def get_position(self) -> Position:
        """
        Construct a position from the entered form information.

        Preserves position identity and account ownership while
        editing. New positions have no assigned position ID.

        Returns:
            Position:
                Unsaved or updated journal position model.
        """
        return Position(
            ticker=self.m_ticker.text().strip().upper(),
            position_id=(self.m_position.position_id if self.m_position is not None else None),
            account_id=self.m_account_id,
            strategy=self.m_strategy.text().strip(),
            catalyst=self.m_catalyst.text().strip(),
            entry_reason=self.m_entry_reason.toPlainText().strip(),
            exit_reason=self.m_exit_reason.toPlainText().strip(),
            mistakes=self.m_mistakes.toPlainText().strip(),
            lessons_learned=self.m_lessons_learned.toPlainText().strip(),
            notes=self.m_notes.toPlainText().strip(),
        )
