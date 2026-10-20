# =============================================================================
# File: app.py
# Purpose: Initializes and launches the STONKS desktop application.
# =============================================================================

import sys

from PySide6.QtWidgets import QApplication

from stonks.gui.main_window import MainWindow
from stonks.gui.styles.theme import STONKS_DARK_THEME
from stonks.journal.journal_context import JournalContext


def main() -> int:
    """
    Launch STONKS with its journal backend initialized.

    Initializes the desktop application and journal dependencies,
    then closes the database connection when the application exits.

    Returns:
        int:
            Application exit status.
    """
    app = QApplication(sys.argv)

    app.setApplicationName("STONKS")
    app.setStyleSheet(STONKS_DARK_THEME)

    with JournalContext() as journal_context:
        window = MainWindow(journal_context)
        window.show()

        return app.exec()


if __name__ == "__main__":
    sys.exit(main())
