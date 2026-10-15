# =============================================================================
# File: test_icons.py
# Purpose: Pytest file for test_icons.py.
# =============================================================================

import pytest

from stonks.gui.icons import get_icon


@pytest.mark.parametrize(
    "name",
    [
        "archive",
        "layout-dashboard",
        "pencil",
        "star",
        "trash",
        "wallet",
    ],
)
def test_svg_icon_loads_and_renders(qtbot, name: str) -> None:
    """Verify SVG assets load and produce valid Qt icon pixmaps."""
    icon = get_icon(name)

    assert not icon.isNull()
    assert not icon.pixmap(24, 24).isNull()
