# =============================================================================
# File: journal_database.py
# Purpose: Manages SQLite connections and journal database initialization.
# =============================================================================

import sqlite3
from pathlib import Path
from typing import Optional

from stonks.config.journal_paths import DATABASE_FILE

SCHEMA_VERSION = 3


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

    Create the complete schema v3 on a fresh database.

    Preserves existing compatible v3 data. Rejects legacy or
    provisional schemas rather than silently altering them.

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

        if current_version not in (0, SCHEMA_VERSION):
            raise RuntimeError(
                f"Unsupported journal database schema version {current_version}. Expected version {SCHEMA_VERSION}."
            )

        if current_version == 0:
            existing_tables = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                AND name NOT LIKE 'sqlite_%'
                """
            ).fetchall()

            if existing_tables:
                raise RuntimeError("Cannot initialize an unversioned database that already contains tables.")

        if current_version == SCHEMA_VERSION:
            existing_tables = {
                row[0]
                for row in connection.execute(
                    """
                    SELECT name FROM sqlite_master
                    WHERE type = 'table'
                    AND name NOT LIKE 'sqlite_%'
                    """
                )
            }
            transaction_columns = {row["name"] for row in connection.execute("PRAGMA table_info(account_transactions)")}
            if "account_transfers" not in existing_tables or "transfer_id" not in transaction_columns:
                raise RuntimeError(
                    "Provisional schema v3 detected without linked transfers. Initialize a fresh development database."
                )

        with connection:
            create_trading_accounts_table(connection)

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS account_opening_cash (
                    account_id INTEGER PRIMARY KEY,
                    amount TEXT NOT NULL,
                    effective_at TEXT NOT NULL,

                    FOREIGN KEY (account_id)
                        REFERENCES trading_accounts(account_id)
                        ON DELETE CASCADE
                ) STRICT
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS positions (
                    position_id INTEGER PRIMARY KEY,
                    account_id INTEGER NOT NULL,

                    ticker TEXT NOT NULL,

                    strategy TEXT NOT NULL DEFAULT '',
                    catalyst TEXT NOT NULL DEFAULT '',

                    entry_reason TEXT NOT NULL DEFAULT '',
                    exit_reason TEXT NOT NULL DEFAULT '',

                    mistakes TEXT NOT NULL DEFAULT '',
                    lessons_learned TEXT NOT NULL DEFAULT '',

                    notes TEXT NOT NULL DEFAULT '',

                    FOREIGN KEY (account_id)
                        REFERENCES trading_accounts(account_id)
                        ON DELETE RESTRICT
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
                CREATE TABLE IF NOT EXISTS account_transfers (
                    transfer_id INTEGER PRIMARY KEY,
                    source_account_id INTEGER NOT NULL,
                    destination_account_id INTEGER NOT NULL,

                    amount TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    notes TEXT NOT NULL DEFAULT '',

                    CHECK (source_account_id != destination_account_id),

                    FOREIGN KEY (source_account_id)
                        REFERENCES trading_accounts(account_id)
                        ON DELETE RESTRICT,

                    FOREIGN KEY (destination_account_id)
                        REFERENCES trading_accounts(account_id)
                        ON DELETE RESTRICT
                ) STRICT
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS account_transactions (
                    transaction_id INTEGER PRIMARY KEY,
                    account_id INTEGER NOT NULL,

                    transaction_type TEXT NOT NULL
                        CHECK (
                            transaction_type IN (
                                'DEPOSIT',
                                'WITHDRAWAL',
                                'FEE',
                                'ADJUSTMENT',
                                'TRANSFER_IN',
                                'TRANSFER_OUT'
                            )
                        ),

                    transfer_id INTEGER DEFAULT NULL,
                    occurred_at TEXT NOT NULL,
                    amount TEXT NOT NULL,

                    notes TEXT NOT NULL DEFAULT '',

                    CHECK (
                        (
                            transaction_type IN ('TRANSFER_IN', 'TRANSFER_OUT')
                            AND transfer_id IS NOT NULL
                        )
                        OR
                        (
                            transaction_type NOT IN ('TRANSFER_IN', 'TRANSFER_OUT')
                            AND transfer_id IS NULL
                        )
                    ),

                    FOREIGN KEY (account_id)
                        REFERENCES trading_accounts(account_id)
                        ON DELETE RESTRICT,

                    FOREIGN KEY (transfer_id)
                        REFERENCES account_transfers(transfer_id)
                        ON DELETE RESTRICT
                ) STRICT
                """
            )

            connection.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_transfer_leg_type
                ON account_transactions(transfer_id, transaction_type)
                WHERE transfer_id IS NOT NULL
                """
            )

            create_account_ownership_triggers(connection)

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


def create_account_ownership_triggers(
    connection: sqlite3.Connection,
) -> None:
    """
    Prevent existing journal records from changing accounts.

    Args:
        connection:
            SQLite connection used to create the triggers.
    """
    connection.execute(
        """
        CREATE TRIGGER IF NOT EXISTS
            trg_positions_account_immutable
        BEFORE UPDATE OF account_id ON positions
        WHEN NEW.account_id != OLD.account_id
        BEGIN
            SELECT RAISE(
                ABORT,
                'Cannot change position account ownership'
            );
        END
        """
    )

    connection.execute(
        """
        CREATE TRIGGER IF NOT EXISTS
            trg_transactions_account_immutable
        BEFORE UPDATE OF account_id ON account_transactions
        WHEN NEW.account_id != OLD.account_id
        BEGIN
            SELECT RAISE(
                ABORT,
                'Cannot change transaction account ownership'
            );
        END
        """
    )
