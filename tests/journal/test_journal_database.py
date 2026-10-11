# =============================================================================
# File: test_journal_database.py
# Purpose: Pytest file for test_journal_database.py.
# =============================================================================

import sqlite3

import pytest

from stonks.journal.journal_database import (
    SCHEMA_VERSION,
    create_connection,
    get_schema_version,
    initialize_database,
)


@pytest.fixture
def connection(tmp_path):
    """Provide an initialized, temporary journal database connection."""
    database_path = tmp_path / "test_journal.db"

    initialize_database(database_path)
    database_connection = create_connection(database_path)

    try:
        yield database_connection
    finally:
        database_connection.close()


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


def test_database_schema_version(tmp_path) -> None:
    """Verify initialization assigns the current schema version."""

    database_path = tmp_path / "test_journal.db"

    initialize_database(database_path)

    connection = create_connection(database_path)

    try:
        assert get_schema_version(connection) == SCHEMA_VERSION

    finally:
        connection.close()


def test_newer_schema_version_is_rejected(tmp_path) -> None:
    """Verify databases from newer STONKS versions are rejected."""

    database_path = tmp_path / "test_journal.db"

    initialize_database(database_path)

    connection = create_connection(database_path)

    try:
        newer_version = SCHEMA_VERSION + 1

        connection.execute(f"PRAGMA user_version = {newer_version}")

    finally:
        connection.close()

    with pytest.raises(
        RuntimeError,
        match="newer than supported",
    ):
        initialize_database(database_path)

    connection = create_connection(database_path)

    try:
        assert get_schema_version(connection) == newer_version

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
        assert get_schema_version(connection) == SCHEMA_VERSION

    finally:
        connection.close()


def test_execution_rejects_invalid_storage_type(
    tmp_path,
) -> None:
    """Verify strict tables reject non-text financial storage."""

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
                        position_id,
                        "BUY",
                        "2026-09-30T16:30:00+00:00",
                        sqlite3.Binary(b"1.375"),
                        "165.50",
                    ),
                )

    finally:
        connection.close()


def test_journal_tables_are_strict(tmp_path) -> None:
    """Verify journal tables use strict SQLite typing."""

    database_path = tmp_path / "test_journal.db"

    initialize_database(database_path)

    connection = create_connection(database_path)

    try:
        rows = connection.execute(
            """
            PRAGMA table_list
            """
        ).fetchall()

        journal_tables = {
            row["name"]: row["strict"]
            for row in rows
            if row["name"]
            in {
                "positions",
                "trade_executions",
                "account_transactions",
            }
        }

        assert journal_tables == {
            "positions": 1,
            "trade_executions": 1,
            "account_transactions": 1,
        }

    finally:
        connection.close()


def test_v2_schema_creates_trading_accounts(tmp_path) -> None:
    """Verify schema v2 creates the trading accounts table."""
    database_path = tmp_path / "journal_v2.db"

    initialize_database(database_path)

    connection = create_connection(database_path)

    try:
        tables = {row["name"] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}

        assert "trading_accounts" in tables
        assert get_schema_version(connection) == 2

    finally:
        connection.close()


def test_v2_positions_require_account_ownership(tmp_path) -> None:
    """Verify positions require a valid trading account."""
    database_path = tmp_path / "journal_v2.db"

    initialize_database(database_path)

    connection = create_connection(database_path)

    try:
        columns = {row["name"]: row for row in connection.execute("PRAGMA table_info(positions)")}

        assert "account_id" in columns
        assert columns["account_id"]["notnull"] == 1

        foreign_keys = connection.execute("PRAGMA foreign_key_list(positions)").fetchall()

        assert any(row["table"] == "trading_accounts" and row["from"] == "account_id" for row in foreign_keys)

    finally:
        connection.close()


def test_v2_transactions_require_account_ownership(tmp_path) -> None:
    """Verify cash transactions require a valid trading account."""
    database_path = tmp_path / "journal_v2.db"

    initialize_database(database_path)

    connection = create_connection(database_path)

    try:
        columns = {row["name"]: row for row in connection.execute("PRAGMA table_info(account_transactions)")}

        assert "account_id" in columns
        assert columns["account_id"]["notnull"] == 1

        foreign_keys = connection.execute("PRAGMA foreign_key_list(account_transactions)").fetchall()

        assert any(row["table"] == "trading_accounts" and row["from"] == "account_id" for row in foreign_keys)

    finally:
        connection.close()


def test_v2_position_account_ownership_is_immutable(connection) -> None:
    """Reject reassignment of a position to another trading account."""
    connection.execute(
        """
        INSERT INTO trading_accounts (account_id, name, account_type)
        VALUES (1, 'Roth IRA', 'ROTH_IRA'),
               (2, 'Cash Account', 'CASH')
        """
    )

    connection.execute(
        """
        INSERT INTO positions (position_id, account_id, ticker)
        VALUES (1, 1, 'NVDA')
        """
    )

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute("UPDATE positions SET account_id = 2 WHERE position_id = 1")


def test_v2_transaction_account_ownership_is_immutable(connection) -> None:
    """Reject reassignment of a cash transaction to another account."""
    connection.execute(
        """
        INSERT INTO trading_accounts (account_id, name, account_type)
        VALUES (1, 'Roth IRA', 'ROTH_IRA'),
               (2, 'Cash Account', 'CASH')
        """
    )

    connection.execute(
        """
        INSERT INTO account_transactions (
            transaction_id,
            account_id,
            transaction_type,
            occurred_at,
            amount
        )
        VALUES (
            1,
            1,
            'DEPOSIT',
            '2026-10-10T12:00:00+00:00',
            '100.00'
        )
        """
    )

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            UPDATE account_transactions
            SET account_id = 2
            WHERE transaction_id = 1
            """
        )
