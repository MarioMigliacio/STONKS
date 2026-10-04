# =============================================================================
# File: test_journal_database.py
# Purpose: Pytest file for test_journal_database.py.
# =============================================================================

import sqlite3

import pytest

from stonks.journal.journal_database import (
    create_connection,
    initialize_database,
)


def test_database_initialization(tmp_path) -> None:
    """Verify journal tables are created successfully."""

    database_path = tmp_path / "test_journal.db"

    initialize_database(database_path)

    connection = create_connection(database_path)

    try:
        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        ).fetchall()

        table_names = {row["name"] for row in rows}

        assert "positions" in table_names
        assert "trade_executions" in table_names
        assert "account_transactions" in table_names

    finally:
        connection.close()


def test_foreign_keys_enabled(tmp_path) -> None:
    """Verify foreign-key enforcement is enabled."""

    database_path = tmp_path / "test_journal.db"

    initialize_database(database_path)

    connection = create_connection(database_path)

    try:
        result = connection.execute("PRAGMA foreign_keys").fetchone()

        assert result[0] == 1

    finally:
        connection.close()


def test_invalid_execution_reference(tmp_path) -> None:
    """Verify executions cannot reference missing positions."""

    database_path = tmp_path / "test_journal.db"

    initialize_database(database_path)

    connection = create_connection(database_path)

    try:
        with pytest.raises(sqlite3.IntegrityError):
            with connection:
                connection.execute(
                    """
                    INSERT INTO trade_executions (
                        position_id,
                        side,
                        executed_at,
                        shares,
                        price
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        999,
                        "BUY",
                        "2026-09-30T16:30:00+00:00",
                        10,
                        "12.50",
                    ),
                )

    finally:
        connection.close()


def test_invalid_share_quantity(tmp_path) -> None:
    """Verify executions cannot contain zero shares."""

    database_path = tmp_path / "test_journal.db"

    initialize_database(database_path)

    connection = create_connection(database_path)

    try:
        with connection:
            connection.execute(
                """
                INSERT INTO positions (ticker)
                VALUES (?)
                """,
                ("NVDA",),
            )

        with pytest.raises(sqlite3.IntegrityError):
            with connection:
                connection.execute(
                    """
                    INSERT INTO trade_executions (
                        position_id,
                        side,
                        executed_at,
                        shares,
                        price
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        1,
                        "BUY",
                        "2026-09-30T16:30:00+00:00",
                        0,
                        "12.50",
                    ),
                )

    finally:
        connection.close()


def test_database_initialization_is_repeatable(tmp_path) -> None:
    """Verify initialization preserves existing records."""

    database_path = tmp_path / "test_journal.db"

    initialize_database(database_path)

    connection = create_connection(database_path)

    try:
        with connection:
            connection.execute(
                """
                INSERT INTO positions (ticker)
                VALUES (?)
                """,
                ("NVDA",),
            )

    finally:
        connection.close()

    initialize_database(database_path)

    connection = create_connection(database_path)

    try:
        result = connection.execute("SELECT COUNT(*) FROM positions").fetchone()

        assert result[0] == 1

    finally:
        connection.close()
