# =============================================================================
# File: main_window.py
# Purpose: Defines the main desktop application window for STONKS.
# =============================================================================

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    """
    Represent the primary STONKS desktop application window.

    Provides the foundation for future application navigation,
    journal management, and market intelligence interfaces.
    """

    def __init__(self) -> None:
        """Initialize the STONKS application window."""
        super().__init__()

        self.setWindowTitle("STONKS - Trading Intelligence")
        self.resize(1200, 800)
        self.setMinimumSize(900, 600)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Construct the initial application interface."""
        central_widget = QWidget(self)

        layout = QVBoxLayout(central_widget)

        title = QLabel("STONKS")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Trading Intelligence Console")
        subtitle.setAlignment(Qt.AlignCenter)

        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch()

        self.setCentralWidget(central_widget)
