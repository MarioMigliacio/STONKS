# =============================================================================
# File: test_journal_integration.py
# Purpose: Pytest file for test_journal_integration.py.
# =============================================================================

import sqlite3
from pathlib import Path

import pytest

from stonks.gui.main_window import MainWindow
from stonks.journal.journal_context import JournalContext
from stonks.journal.persistence.journal_database import SCHEMA_VERSION, get_schema_version


def test_main_window_receives_journal_context(
    qtbot,
    tmp_path: Path,
) -> None:
    """Verify the main window receives the initialized journal context."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal_context:
        window = MainWindow(journal_context)
        qtbot.addWidget(window)

        assert window.m_journal_context is journal_context
        assert window.m_journal_context.m_repository is journal_context.m_repository
        assert window.m_journal_context.m_service is journal_context.m_service


def test_journal_context_connection_lifecycle(
    tmp_path: Path,
) -> None:
    """Verify journal initialization and connection cleanup."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal_context:
        connection = journal_context.m_connection

        assert database_path.exists()
        assert get_schema_version(connection) == SCHEMA_VERSION

    with pytest.raises(sqlite3.ProgrammingError):
        connection.execute("SELECT 1")
