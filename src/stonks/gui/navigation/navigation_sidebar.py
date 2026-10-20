# =============================================================================
# File: navigation_sidebar.py
# Purpose: Provides sidebar navigation for the STONKS application.
# =============================================================================

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class NavigationSidebar(QFrame):
    """
    Represent the persistent STONKS navigation sidebar.

    Provides navigation controls and visually identifies the
    currently selected application page.

    Attributes:
        m_button_group:
            Exclusive button group managing navigation selection.
    """

    navigation_requested = Signal(str)

    def __init__(self) -> None:
        """Initialize the sidebar and navigation controls."""
        super().__init__()

        self.setObjectName("navigationSidebar")
        self.setFixedWidth(220)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Construct the sidebar layout and navigation buttons."""
        layout = QVBoxLayout(self)

        title = QLabel("STONKS")
        title.setObjectName("applicationTitle")

        layout.addWidget(title)
        layout.addSpacing(20)

        self.m_button_group = QButtonGroup(self)
        self.m_button_group.setExclusive(True)

        page_definitions = {
            "dashboard": "Dashboard",
            "journal": "Journal",
            "accounts": "Accounts",
            "scanner": "Scanner",
            "cia": "C.I.A.",
        }

        for page_name, display_name in page_definitions.items():
            button = QPushButton(display_name)
            button.setCheckable(True)

            self.m_button_group.addButton(button)
            layout.addWidget(button)

            button.clicked.connect(lambda checked=False, name=page_name: self.navigation_requested.emit(name))

            if page_name == "dashboard":
                button.setChecked(True)

        layout.addStretch()
