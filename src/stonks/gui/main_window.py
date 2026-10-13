# =============================================================================
# File: main_window.py
# Purpose: Defines the main desktop application window for STONKS.
# =============================================================================

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from stonks.gui.navigation.navigation_sidebar import NavigationSidebar


class MainWindow(QMainWindow):
    """
    Represent the primary STONKS desktop application window.

    Coordinates the persistent navigation sidebar and central
    application content.
    """

    def __init__(self) -> None:
        """Initialize the STONKS application window."""
        super().__init__()

        self.setWindowTitle("STONKS - Trading Intelligence")
        self.resize(1200, 800)
        self.setMinimumSize(900, 600)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Construct the main application shell."""
        central_widget = QWidget(self)

        main_layout = QHBoxLayout(central_widget)

        self.m_sidebar = NavigationSidebar()

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        title = QLabel("Welcome to STONKS")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Trading Intelligence Console")
        subtitle.setAlignment(Qt.AlignCenter)

        content_layout.addStretch()
        content_layout.addWidget(title)
        content_layout.addWidget(subtitle)
        content_layout.addStretch()

        main_layout.addWidget(self.m_sidebar)
        main_layout.addWidget(content_widget, stretch=1)

        self.setCentralWidget(central_widget)
