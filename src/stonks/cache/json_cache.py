# =============================================================================
# File: json_cache.py
# Purpose: Provides JSON read/write helpers for local cache data.
# =============================================================================

import json
from pathlib import Path
from typing import Any, Optional


def read_json(file_path: Path) -> Optional[dict[str, Any]]:
    """Read JSON data from a file if it exists."""

    if not file_path.exists():
        return None

    with open(file_path, mode="r", encoding="utf-8") as file:
        return json.load(file)


def write_json(file_path: Path, data: dict[str, Any]):
    """Write JSON data to a file."""

    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, mode="w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
