# =============================================================================
# File: journal_backup.py
# Purpose: Creates and verifies compressed backups of journal data.
# =============================================================================

import logging
import zipfile
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from stonks.config.journal_paths import (
    BACKUP_DIRECTORY,
    DATA_DIRECTORY,
)
from stonks.log_manager import configure_logging

logger = logging.getLogger(__name__)


def create_backup() -> Path:
    """
    Create and verify a compressed backup of journal CSV files.

    Collects journal CSV files, creates a uniquely named ZIP
    archive, and verifies its integrity before returning.
    Removes incomplete archives if backup creation fails.

    Returns:
        Path:
            Filesystem path of the verified ZIP archive.

    Raises:
        FileNotFoundError:
            If no journal CSV files are available.

        OSError:
            If a file or directory operation fails.

        zipfile.BadZipFile:
            If archive integrity verification fails.
    """
    csv_files = sorted(DATA_DIRECTORY.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(f"No journal CSV files found in {DATA_DIRECTORY}")

    BACKUP_DIRECTORY.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    unique_id = uuid4().hex[:8]

    zip_path = BACKUP_DIRECTORY / f"stonks_journal_{timestamp}_{unique_id}.zip"

    try:
        with zipfile.ZipFile(
            zip_path,
            mode="x",
            compression=zipfile.ZIP_DEFLATED,
        ) as archive:
            for file_path in csv_files:
                archive.write(
                    file_path,
                    arcname=file_path.name,
                )

        with zipfile.ZipFile(zip_path, mode="r") as archive:
            corrupted_file = archive.testzip()

            if corrupted_file is not None:
                raise zipfile.BadZipFile(f"Corrupted backup entry: {corrupted_file}")

            archived_files = set(archive.namelist())
            expected_files = {file_path.name for file_path in csv_files}

            if archived_files != expected_files:
                raise zipfile.BadZipFile("Backup contents do not match source files.")

    except Exception:
        if zip_path.exists():
            zip_path.unlink()

        logger.exception("Failed to create journal backup.")
        raise

    logger.info(
        "Journal backup verified: %d files in %s",
        len(csv_files),
        zip_path,
    )

    return zip_path


def main() -> None:
    """
    Run the journal backup command-line utility.

    Configures logging, creates a verified backup,
    and reports the resulting archive location.

    Returns:
        None.
    """
    configure_logging()

    backup_path = create_backup()

    print(f"Journal backup created: {backup_path}")


if __name__ == "__main__":
    main()
