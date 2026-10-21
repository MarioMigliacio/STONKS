# =============================================================================
# File: test_icons.py
# Purpose: Pytest file for test_icons.py.
# =============================================================================

import pytest

from stonks.gui.icons import get_icon


@pytest.mark.parametrize(
    "name",
    [
        "archive-restore",
        "archive",
        "arrow-left",
        "arrow-right",
        "calendar-days",
        "chevron-down",
        "chevron-left",
        "chevron-right",
        "chevron-up",
        "ellipsis-vertical",
        "ellipsis",
        "layout-dashboard",
        "pencil",
        "plus",
        "star",
        "trash",
        "trash-danger",
        "triangle-alert",
        "wallet",
    ],
)
def test_svg_icon_loads_and_renders(qtbot, name: str) -> None:
    """Verify SVG assets load and produce valid Qt icon pixmaps."""
    icon = get_icon(name)

    assert not icon.isNull()
    assert not icon.pixmap(24, 24).isNull()
