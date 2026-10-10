# =============================================================================
# File: journal_database.py
# Purpose: Manages SQLite connections and journal database initialization.
# =============================================================================

import sqlite3
from pathlib import Path
from typing import Optional

from stonks.config.journal_paths import DATABASE_FILE

SCHEMA_VERSION = 1


def create_connection(
    database_path: Optional[Path] = None,
) -> sqlite3.Connection:
    """
    Create a configured SQLite database connection.

    Enables foreign-key enforcement and configures database
    rows to support column-name access.

    Args:
        database_path:
            Optional database location. Uses the configured
            journal database path when not provided.

    Returns:
        sqlite3.Connection:
            Configured SQLite connection.
    """
    path = database_path if database_path is not None else DATABASE_FILE

    path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(str(path))

    try:
        connection.row_factory = sqlite3.Row

        connection.execute("PRAGMA foreign_keys = ON")

        return connection

    except Exception:
        connection.close()
        raise


def get_schema_version(
    connection: sqlite3.Connection,
) -> int:
    """
    Return the journal database schema version.

    Args:
        connection:
            SQLite connection whose schema version is requested.

    Returns:
        int:
            Current SQLite user schema version.
    """
    row = connection.execute("PRAGMA user_version").fetchone()

    return int(row[0])


def initialize_database(
    database_path: Optional[Path] = None,
) -> None:
    """
    Initialize the journal database schema.

    Creates position, execution, and account transaction
    tables if they do not already exist.

    Existing tables and records are preserved.

    Args:
        database_path:
            Optional database location. Uses the configured
            journal database path when not provided.

    Returns:
        None.
    """
    connection = create_connection(database_path)

    try:
        current_version = get_schema_version(connection)

        if current_version > SCHEMA_VERSION:
            raise RuntimeError(
                f"Journal database schema version {current_version} is newer than supported version {SCHEMA_VERSION}."
            )

        with connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS positions (
                    position_id INTEGER PRIMARY KEY,

                    ticker TEXT NOT NULL,

                    strategy TEXT NOT NULL DEFAULT '',
                    catalyst TEXT NOT NULL DEFAULT '',

                    entry_reason TEXT NOT NULL DEFAULT '',
                    exit_reason TEXT NOT NULL DEFAULT '',

                    mistakes TEXT NOT NULL DEFAULT '',
                    lessons_learned TEXT NOT NULL DEFAULT '',

                    notes TEXT NOT NULL DEFAULT ''
                ) STRICT
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS trade_executions (
                    execution_id INTEGER PRIMARY KEY,
                    position_id INTEGER NOT NULL,

                    side TEXT NOT NULL
                        CHECK (side IN ('BUY', 'SELL')),

                    executed_at TEXT NOT NULL,

                    shares TEXT NOT NULL,

                    price TEXT NOT NULL,
                    fees TEXT NOT NULL DEFAULT '0.00',

                    notes TEXT NOT NULL DEFAULT '',

                    FOREIGN KEY (position_id)
                        REFERENCES positions(position_id)
                        ON DELETE CASCADE
                ) STRICT
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS account_transactions (
                    transaction_id INTEGER PRIMARY KEY,

                    transaction_type TEXT NOT NULL
                        CHECK (
                            transaction_type IN (
                                'DEPOSIT',
                                'WITHDRAWAL',
                                'FEE',
                                'ADJUSTMENT'
                            )
                        ),

                    occurred_at TEXT NOT NULL,
                    amount TEXT NOT NULL,

                    notes TEXT NOT NULL DEFAULT ''
                ) STRICT
                """
            )

            connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    finally:
        connection.close()


def create_trading_accounts_table(
    connection: sqlite3.Connection,
) -> None:
    """
    Create the trading accounts table and its constraints.

    Args:
        connection:
            SQLite connection used to create the table.
    """
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS trading_accounts (
            account_id INTEGER PRIMARY KEY,

            name TEXT NOT NULL
                CHECK (length(trim(name)) > 0),

            account_type TEXT NOT NULL
                CHECK (
                    account_type IN (
                        'ROTH_IRA',
                        'TRADITIONAL_IRA',
                        'CASH',
                        'MARGIN',
                        'OTHER'
                    )
                ),

            broker TEXT NOT NULL DEFAULT '',

            is_active INTEGER NOT NULL DEFAULT 1
                CHECK (is_active IN (0, 1)),

            is_default INTEGER NOT NULL DEFAULT 0
                CHECK (is_default IN (0, 1)),

            CHECK (NOT (is_default = 1 AND is_active = 0))
        ) STRICT
        """
    )

    connection.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_trading_accounts_default
        ON trading_accounts(is_default)
        WHERE is_default = 1
        """
    )
