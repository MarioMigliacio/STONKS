# =============================================================================
# File: scanner_cli.py
# Purpose: Run the legacy STONKS scanner from the command line.
# =============================================================================

from stonks.log_manager import configure_logging
from stonks.scanner.filters import scan_stocks


def main() -> None:
    """Run the scanner and display matching stock candidates."""
    configure_logging()

    print("=== STONKS Scanner ===")

    results = scan_stocks()

    print("\n=== RESULTS ===")

    if not results:
        print("No matching stocks found.")
        return

    for candidate in results:
        print(candidate)


if __name__ == "__main__":
    main()
