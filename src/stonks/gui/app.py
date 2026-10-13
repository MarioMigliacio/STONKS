# =============================================================================
# File: app.py
# Purpose: Initializes and launches the STONKS desktop application.
# =============================================================================

import sys

from PySide6.QtWidgets import QApplication

from stonks.gui.main_window import MainWindow


def main() -> int:
    """
    Launch the STONKS desktop application.

    Returns:
        int:
            Application exit status.
    """
    app = QApplication(sys.argv)

    app.setApplicationName("STONKS")

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
