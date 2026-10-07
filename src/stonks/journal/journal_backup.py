# =============================================================================
# File: journal_backup.py
# Purpose: Creates and manages SQLite journal database backups.
# =============================================================================

import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from stonks.config.journal_paths import (
    BACKUP_DIRECTORY,
    DATABASE_FILE,
)
from stonks.journal.journal_database import (
    SCHEMA_VERSION,
    get_schema_version,
)


def create_database_backup(
    database_path: Optional[Path] = None,
    backup_directory: Optional[Path] = None,
) -> Path:
    """
    Create a consistent backup of the journal database.

    Uses SQLite's native backup API to safely copy the database,
    including databases that may currently be open by STONKS.

    Args:
        database_path:
            Optional journal database to back up. Uses the
            configured journal database when not provided.

        backup_directory:
            Optional destination directory. Uses the configured
            backup directory when not provided.

    Returns:
        Path:
            Location of the created SQLite backup.

    Raises:
        FileNotFoundError:
            If the source journal database does not exist.
    """
    source_path = database_path if database_path is not None else DATABASE_FILE

    destination_directory = backup_directory if backup_directory is not None else BACKUP_DIRECTORY

    if not source_path.exists():
        raise FileNotFoundError(f"Journal database does not exist: {source_path}")

    destination_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")

    backup_path = destination_directory / f"stonks_journal_{timestamp}.db"

    source_connection = sqlite3.connect(str(source_path))
    backup_connection = sqlite3.connect(str(backup_path))

    try:
        with closing(sqlite3.connect(str(source_path))) as source_connection:
            with closing(sqlite3.connect(str(backup_path))) as backup_connection:
                source_connection.backup(backup_connection)

    except Exception:
        if backup_path.exists():
            backup_path.unlink()

        raise

    return backup_path


def validate_database_backup(
    backup_path: Path,
) -> None:
    """
    Validate a journal database backup before restoration.

    Verifies that the backup exists, is a readable SQLite
    database, contains the required journal tables, and uses
    a supported schema version.

    Args:
        backup_path:
            SQLite backup database to validate.

    Raises:
        FileNotFoundError:
            If the backup file does not exist.

        ValueError:
            If the backup is not a valid journal database.
    """
    if not backup_path.exists():
        raise FileNotFoundError(f"Journal backup does not exist: {backup_path}")

    required_tables = {
        "positions",
        "trade_executions",
        "account_transactions",
    }

    try:
        with closing(sqlite3.connect(str(backup_path))) as connection:
            result = connection.execute("PRAGMA integrity_check").fetchone()

            if result is None or result[0] != "ok":
                raise ValueError("Journal backup failed SQLite integrity validation.")

            rows = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            ).fetchall()

            table_names = {row[0] for row in rows}

            if not required_tables.issubset(table_names):
                raise ValueError("Backup does not contain the required journal tables.")

            schema_version = get_schema_version(connection)

            if schema_version != SCHEMA_VERSION:
                raise ValueError(
                    f"Backup schema version {schema_version} does not match supported version {SCHEMA_VERSION}."
                )

    except sqlite3.DatabaseError as exc:
        raise ValueError("Backup is not a valid SQLite database.") from exc


def restore_database_backup(
    backup_path: Path,
    database_path: Optional[Path] = None,
    backup_directory: Optional[Path] = None,
) -> Path:
    """
    Restore the journal database from a validated backup.

    Creates a safety backup of the current journal before
    replacing its contents with the selected backup.

    Args:
        backup_path:
            Journal database backup to restore.

        database_path:
            Optional destination journal database. Uses the
            configured journal database when not provided.

        backup_directory:
            Optional directory for the pre-restore safety
            backup. Uses the configured backup directory when
            not provided.

    Returns:
        Path:
            Location of the pre-restore safety backup.

    Raises:
        FileNotFoundError:
            If the selected backup or destination journal
            database does not exist.

        ValueError:
            If the selected backup is not a valid journal
            database.
    """
    destination_path = database_path if database_path is not None else DATABASE_FILE

    validate_database_backup(backup_path)

    if not destination_path.exists():
        raise FileNotFoundError(f"Journal database does not exist: {destination_path}")

    safety_backup_path = create_database_backup(
        database_path=destination_path,
        backup_directory=backup_directory,
    )

    with closing(sqlite3.connect(str(backup_path))) as source_connection:
        with closing(sqlite3.connect(str(destination_path))) as destination_connection:
            source_connection.backup(destination_connection)

    validate_database_backup(destination_path)

    return safety_backup_path
