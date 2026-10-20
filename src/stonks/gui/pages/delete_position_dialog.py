# =============================================================================
# File: delete_position_dialog.py
# Purpose: Confirms permanent deletion of an empty journal position.
# =============================================================================

from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from stonks.gui.icons import get_icon
from stonks.journal.models.position import Position


class DeletePositionDialog(QDialog):
    """
    Confirm permanent deletion of a journal trading position.

    Displays the selected position's identity and explains that
    journal metadata will be permanently removed. The calling
    page and journal service remain responsible for validating
    whether the position can be deleted.

    Attributes:
        m_position:
            Position selected for permanent deletion.

        m_warning_icon:
            Red warning icon indicating a destructive action.

        m_cancel_button:
            Button that rejects the deletion request.

        m_delete_button:
            Danger-styled button that confirms deletion.
    """

    def __init__(
        self,
        position: Position,
        parent=None,
    ) -> None:
        """
        Initialize the position deletion confirmation dialog.

        Args:
            position:
                Position that the user intends to delete.

            parent:
                Optional parent Qt widget.
        """
        super().__init__(parent)

        self.m_position = position

        self.setWindowTitle("Delete Trading Position")
        self.setMinimumWidth(440)
        self.setModal(True)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Construct the destructive-action confirmation interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # Warning heading.
        heading_layout = QHBoxLayout()

        self.m_warning_icon = QLabel()
        self.m_warning_icon.setPixmap(get_icon("triangle-alert").pixmap(QSize(32, 32)))

        heading = QLabel("Delete Trading Position?")
        heading.setObjectName("dangerHeading")

        heading_layout.addWidget(self.m_warning_icon)
        heading_layout.addWidget(heading)
        heading_layout.addStretch()

        layout.addLayout(heading_layout)

        # Position identification.
        description = QLabel(f"You are about to permanently delete the {self.m_position.ticker} journal position.")
        description.setWordWrap(True)
        layout.addWidget(description)

        position_id = str(self.m_position.position_id) if self.m_position.position_id is not None else "Not assigned"

        details = QLabel(f"Ticker: {self.m_position.ticker}\nPosition ID: {position_id}\nTrade executions: 0")
        details.setObjectName("deletionSummary")
        layout.addWidget(details)

        # Deletion warning.
        warning = QLabel(
            "Journal notes, trade reasoning, and other position "
            "details will be permanently removed.\n\n"
            "Positions containing trade executions cannot be deleted."
        )
        warning.setWordWrap(True)
        warning.setObjectName("dangerWarning")
        layout.addWidget(warning)

        # Confirmation buttons.
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.m_cancel_button = QPushButton("Cancel")

        self.m_delete_button = QPushButton("Delete Position")
        self.m_delete_button.setObjectName("dangerButton")
        self.m_delete_button.setIcon(get_icon("trash"))

        button_layout.addWidget(self.m_cancel_button)
        button_layout.addWidget(self.m_delete_button)

        layout.addLayout(button_layout)

        # Connect actions.
        self.m_cancel_button.clicked.connect(self.reject)
        self.m_delete_button.clicked.connect(self.accept)

        self.m_cancel_button.setFocus()
