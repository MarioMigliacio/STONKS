# =============================================================================
# File: placeholder_page.py
# Purpose: Provides reusable placeholder pages for STONKS navigation.
# =============================================================================

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)


class PlaceholderPage(QWidget):
    """
    Represent a temporary application page.

    Provides a consistent layout for application features
    that have not yet received their dedicated GUI.
    """

    def __init__(self, title: str) -> None:
        """
        Initialize the placeholder page.

        Args:
            title:
                Display title identifying the application page.
        """
        super().__init__()

        layout = QVBoxLayout(self)

        label = QLabel(title)
        label.setAlignment(Qt.AlignCenter)

        layout.addWidget(label)
