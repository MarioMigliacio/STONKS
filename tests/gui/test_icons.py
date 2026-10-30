# =============================================================================
# File: test_icons.py
# Purpose: Pytest file for test_icons.py.
# =============================================================================

import pytest

from stonks.gui.icons import get_icon


@pytest.mark.parametrize(
    "name",
    [
        "activity",
        "archive-restore",
        "archive",
        "arrow-left",
        "arrow-right",
        "calendar-days",
        "check",
        "chevron-down",
        "chevron-left",
        "chevron-right",
        "chevron-up",
        "clock-3",
        "ellipsis-vertical",
        "ellipsis",
        "external-link",
        "file-search",
        "file-text",
        "gauge",
        "layers",
        "layout-dashboard",
        "newspaper",
        "pencil",
        "play",
        "plus",
        "radar",
        "rotate-ccw-clock",
        "scan-search",
        "search-check",
        "shield-alert",
        "sliders-horizontal",
        "square",
        "star",
        "trash",
        "trending-down",
        "trending-up",
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
