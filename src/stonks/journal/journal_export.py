# =============================================================================
# File: journal_export.py
# Purpose: Exports journal database records to human-readable CSV files.
# =============================================================================

import csv
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from stonks.config.journal_paths import (
    DATABASE_FILE,
    EXPORT_DIRECTORY,
)

JOURNAL_TABLES = (
    "positions",
    "trade_executions",
    "account_transactions",
)


def _export_table_to_csv(
    connection: sqlite3.Connection,
    table_name: str,
    output_path: Path,
) -> None:
    """
    Export a journal database table to a CSV file.

    Args:
        connection:
            Open SQLite connection containing the journal table.

        table_name:
            Name of the table to export.

        output_path:
            Destination path for the generated CSV file.
    """
    cursor = connection.execute(f"SELECT * FROM {table_name}")

    column_names = [description[0] for description in cursor.description]

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow(column_names)
        writer.writerows(cursor.fetchall())


def export_journal_to_csv(
    database_path: Optional[Path] = None,
    export_directory: Optional[Path] = None,
) -> Path:
    """
    Export the journal database to human-readable CSV files.

    Creates a timestamped export directory containing one CSV
    file for each journal database table.

    Args:
        database_path:
            Optional journal database to export. Uses the
            configured journal database when not provided.

        export_directory:
            Optional parent directory for generated exports.
            Uses the configured export directory when not
            provided.

    Returns:
        Path:
            Location of the created journal export directory.

    Raises:
        FileNotFoundError:
            If the journal database does not exist.
    """
    source_path = database_path if database_path is not None else DATABASE_FILE

    destination_directory = export_directory if export_directory is not None else EXPORT_DIRECTORY

    if not source_path.exists():
        raise FileNotFoundError(f"Journal database does not exist: {source_path}")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")

    export_path = destination_directory / f"journal_{timestamp}"

    export_path.mkdir(
        parents=True,
        exist_ok=False,
    )

    try:
        with closing(sqlite3.connect(str(source_path))) as connection:
            for table_name in JOURNAL_TABLES:
                _export_table_to_csv(
                    connection=connection,
                    table_name=table_name,
                    output_path=(export_path / f"{table_name}.csv"),
                )

    except Exception:
        for export_file in export_path.iterdir():
            export_file.unlink()

        export_path.rmdir()
        raise

    return export_path
