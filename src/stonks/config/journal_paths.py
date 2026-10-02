# =============================================================================
# File: journal_paths.py
# Purpose: Defines centralized filesystem paths for journal data.
# =============================================================================

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATA_DIRECTORY = PROJECT_ROOT / "data" / "journal"
BACKUP_DIRECTORY = PROJECT_ROOT / "backups"

ORDERS_FILE = DATA_DIRECTORY / "orders.csv"
SNAPSHOTS_FILE = DATA_DIRECTORY / "account_snapshots.csv"
