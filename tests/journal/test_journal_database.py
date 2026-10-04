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
                        "10",
                        "12.50",
                    ),
                )

    finally:
        connection.close()


def test_fractional_share_storage(tmp_path) -> None:
    """Verify SQLite preserves fractional share quantities."""

    database_path = tmp_path / "test_journal.db"

    initialize_database(database_path)

    connection = create_connection(database_path)

    try:
        with connection:
            cursor = connection.execute(
                """
                INSERT INTO positions (ticker)
                VALUES (?)
                """,
                ("AMD",),
            )

            position_id = cursor.lastrowid

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
                    position_id,
                    "BUY",
                    "2026-09-30T16:30:00+00:00",
                    "1.375",
                    "165.50",
                ),
            )

        row = connection.execute(
            """
            SELECT shares, typeof(shares) AS storage_type
            FROM trade_executions
            WHERE position_id = ?
            """,
            (position_id,),
        ).fetchone()

        assert row is not None
        assert row["shares"] == "1.375"
        assert row["storage_type"] == "text"

    finally:
        connection.close()


def test_share_column_uses_text(tmp_path) -> None:
    """Verify share quantities use exact text storage."""

    database_path = tmp_path / "test_journal.db"

    initialize_database(database_path)

    connection = create_connection(database_path)

    try:
        columns = connection.execute(
            """
            PRAGMA table_info(trade_executions)
            """
        ).fetchall()

        share_column = next(row for row in columns if row["name"] == "shares")

        assert share_column["type"] == "TEXT"
        assert share_column["notnull"] == 1

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
