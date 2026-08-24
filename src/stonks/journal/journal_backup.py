# =============================================================================
# File: journal_backup.py
# Purpose: Creates compressed backups of journal data.
# =============================================================================

import zipfile
from datetime import datetime
from pathlib import Path

DATA_DIRECTORY = Path("data/journal")
BACKUP_DIRECTORY = Path("backups")


def create_backup():
    """
    Create a timestamped ZIP backup of journal data.
    """

    BACKUP_DIRECTORY.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    zip_path = BACKUP_DIRECTORY / f"stonks_journal_{timestamp}.zip"

    with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in DATA_DIRECTORY.glob("*.csv"):
            archive.write(file_path, arcname=file_path.name)

    print("")
    print("Backup created:")
    print(zip_path)


def main():
    create_backup()


if __name__ == "__main__":
    main()
