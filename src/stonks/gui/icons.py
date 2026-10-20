# =============================================================================
# File: icons.py
# Purpose: Provides centralized access to STONKS GUI icon assets.
# =============================================================================

from pathlib import Path

from PySide6 import QtSvg  # noqa: F401
from PySide6.QtGui import QIcon

ICON_DIRECTORY = Path(__file__).resolve().parent / "assets" / "icons"


def get_icon(name: str) -> QIcon:
    """
    Retrieve a GUI icon by its asset name.

    Args:
        name:
            Icon filename without the .svg extension.

    Returns:
        QIcon:
            Icon loaded from the application's assets directory.

    Raises:
        FileNotFoundError:
            If the requested icon does not exist.
    """
    icon_path = ICON_DIRECTORY / f"{name}.svg"

    if not icon_path.is_file():
        raise FileNotFoundError(f"GUI icon not found: {icon_path}")

    return QIcon(str(icon_path))
