# =============================================================================
# File: app.py
# Purpose: Initializes and launches the STONKS desktop application.
# =============================================================================

import sys

from PySide6.QtWidgets import QApplication

from stonks.gui.main_window import MainWindow
from stonks.gui.styles.theme import STONKS_DARK_THEME


def main() -> int:
    """
    Launch the STONKS desktop application.

    Returns:
        int:
            Application exit status.
    """
    app = QApplication(sys.argv)

    app.setApplicationName("STONKS")
    app.setStyleSheet(STONKS_DARK_THEME)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
