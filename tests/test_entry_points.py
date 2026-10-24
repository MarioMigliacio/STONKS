# =============================================================================
# File: test_entry_points.py
# Purpose: Verify desktop and scanner entry-point delegation.
# =============================================================================

from unittest.mock import patch

from stonks import __main__ as desktop_entry
from stonks import scanner_cli


def test_default_entry_point_launches_desktop():
    """Verify that the default entry point delegates to the GUI."""
    with patch.object(desktop_entry, "configure_logging"):
        with patch("stonks.gui.app.main", return_value=0) as launch:
            result = desktop_entry.main()

    launch.assert_called_once_with()
    assert result == 0


def test_desktop_entry_point_propagates_exit_status():
    """Verify that the desktop exit status is preserved."""
    with patch.object(desktop_entry, "configure_logging"):
        with patch("stonks.gui.app.main", return_value=2):
            result = desktop_entry.main()

    assert result == 2


def test_scanner_entry_point_preserves_results(capsys):
    """Verify that the scanner displays returned candidates."""
    with patch.object(scanner_cli, "configure_logging"):
        with patch.object(
            scanner_cli,
            "scan_stocks",
            return_value=["AAPL", "NVDA"],
        ):
            scanner_cli.main()

    output = capsys.readouterr().out

    assert "STONKS Scanner" in output
    assert "AAPL" in output
    assert "NVDA" in output


def test_scanner_entry_point_handles_no_matches(capsys):
    """Verify that the scanner reports an empty result set."""
    with patch.object(scanner_cli, "configure_logging"):
        with patch.object(scanner_cli, "scan_stocks", return_value=[]):
            scanner_cli.main()

    assert "No matching stocks found." in capsys.readouterr().out
