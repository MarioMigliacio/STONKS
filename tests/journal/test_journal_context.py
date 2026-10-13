# =============================================================================
# File: test_journal_context.py
# Purpose: Pytest file for test_journal_context.py.
# =============================================================================

import sqlite3
from pathlib import Path

import pytest

from stonks.journal.journal_context import JournalContext
from stonks.journal.persistence.journal_database import get_schema_version


def test_journal_context_initializes_database(
    tmp_path: Path,
) -> None:
    """Verify the context initializes a usable journal database."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        assert database_path.exists()

        assert get_schema_version(journal.m_connection) == 2

        assert journal.m_repository.get_trading_accounts() == []


def test_journal_context_enables_foreign_keys(
    tmp_path: Path,
) -> None:
    """Verify the context enables SQLite foreign-key enforcement."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        row = journal.m_connection.execute("PRAGMA foreign_keys").fetchone()

        assert row[0] == 1


def test_journal_context_closes_connection(
    tmp_path: Path,
) -> None:
    """Verify exiting the context closes its database connection."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        connection = journal.m_connection

    with pytest.raises(sqlite3.ProgrammingError):
        connection.execute("SELECT 1")
