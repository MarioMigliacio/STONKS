# =============================================================================
# File: journal_backup.py
# Purpose: Creates compressed backups of journal data.
# =============================================================================

import logging
import zipfile
from datetime import datetime
from pathlib import Path

from stonks.log_manager import configure_logging

logger = logging.getLogger("stonks.journal.journal_backup")

DATA_DIRECTORY = Path("data/journal")
BACKUP_DIRECTORY = Path("backups")


def create_backup() -> None:
    """
    Create a timestamped ZIP archive of the journal's CSV files.

    Creates the backup directory if necessary, collects all CSV
    files from the journal data directory, and writes them to
    a compressed archive. Logs the archive path and the number
    of files included.

    Returns:
        None.

    Raises:
        OSError:
            If the backup directory or archive cannot be
            created, or a source file cannot be read.
    """

    BACKUP_DIRECTORY.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    zip_path = BACKUP_DIRECTORY / f"stonks_journal_{timestamp}.zip"
    files_backed_up = 0

    with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in DATA_DIRECTORY.glob("*.csv"):
            archive.write(file_path, arcname=file_path.name)
            files_backed_up += 1

    logger.info(
        "Journal backup created with %d files: %s",
        files_backed_up,
        zip_path,
    )


def main() -> None:
    """
    Run the journal backup command-line utility.

    Configures application logging and invokes the journal
    backup operation.

    Returns:
        None.
    """
    configure_logging()
    create_backup()


if __name__ == "__main__":
    main()
