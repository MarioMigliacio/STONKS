# =============================================================================
# File: json_cache.py
# Purpose: Provides JSON read/write helpers for local cache data.
# =============================================================================

import json
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


def read_json(file_path: Path) -> Optional[dict[str, Any]]:
    """Read JSON data from a file if it exists."""

    if not file_path.exists():
        logger.debug(
            "Cache file does not exist: %s",
            file_path,
        )
        return None

    logger.debug(
        "Reading JSON cache file: %s",
        file_path,
    )

    with open(file_path, mode="r", encoding="utf-8") as file:
        return json.load(file)


def write_json(file_path: Path, data: dict[str, Any]):
    """Write JSON data to a file."""

    file_path.parent.mkdir(parents=True, exist_ok=True)

    logger.debug(
        "Writing JSON cache file: %s",
        file_path,
    )

    with open(file_path, mode="w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
