# =============================================================================
# File: journal_database.py
# Purpose: Manages SQLite connections and journal database initialization.
# =============================================================================

import sqlite3
from pathlib import Path
from typing import Optional

from stonks.config.journal_paths import DATABASE_FILE


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
                )
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
                )
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
                )
                """
            )

    finally:
        connection.close()
