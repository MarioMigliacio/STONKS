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
