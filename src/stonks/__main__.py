# =============================================================================
# File: __main__.py
# Purpose: Launch the STONKS desktop application.
# =============================================================================

from stonks.log_manager import configure_logging


def main() -> int:
    """
    Launch the STONKS desktop application.

    Returns:
        int: Application exit status.
    """
    configure_logging()

    from stonks.gui.app import main as launch_desktop

    return launch_desktop()


if __name__ == "__main__":
    raise SystemExit(main())
