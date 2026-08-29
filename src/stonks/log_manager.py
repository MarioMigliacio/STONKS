# =============================================================================
# File: log_manager.py
# Purpose: Configures application logging for STONKS.
# =============================================================================

import logging
from pathlib import Path

from stonks.config import settings

LOG_DIRECTORY = Path("logs")
LOG_FILE = LOG_DIRECTORY / "stonks.log"


def configure_logging() -> None:
    """Configure console and file logging for STONKS."""

    stonks_logger = logging.getLogger("stonks")

    if stonks_logger.handlers:
        return

    LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)

    console_log_level = getattr(
        logging,
        settings.CONSOLE_LOG_LEVEL.upper(),
        logging.INFO,
    )

    file_log_level = getattr(
        logging,
        settings.FILE_LOG_LEVEL.upper(),
        logging.DEBUG,
    )

    stonks_logger.setLevel(logging.DEBUG)
    stonks_logger.propagate = False

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s.%(funcName)s | %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_log_level)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8")
    file_handler.setLevel(file_log_level)
    file_handler.setFormatter(formatter)

    stonks_logger.addHandler(console_handler)
    stonks_logger.addHandler(file_handler)
