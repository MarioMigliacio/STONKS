# =============================================================================
# File: journal_paths.py
# Purpose: Defines filesystem paths for journal data and backups.
# =============================================================================

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATA_DIRECTORY = PROJECT_ROOT / "data" / "journal"
BACKUP_DIRECTORY = PROJECT_ROOT / "backups"

DATABASE_FILE = DATA_DIRECTORY / "stonks_journal.db"
