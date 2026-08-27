# =============================================================================
# File: log_manager.py
# Purpose: Configures application logging for STONKS.
# =============================================================================

import logging

from stonks.config import settings


def configure_logging() -> None:
    """Configure STONKS application logging."""

    log_level = getattr(
        logging,
        settings.LOG_LEVEL.upper(),
        logging.INFO,
    )

    stonks_logger = logging.getLogger("stonks")
    stonks_logger.setLevel(log_level)

    if stonks_logger.handlers:
        return

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    stonks_logger.addHandler(console_handler)
    stonks_logger.propagate = False
