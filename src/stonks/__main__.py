# =============================================================================
# File: __main__.py
# Purpose: Entry point for running STONKS as a Python module.
# =============================================================================

from stonks.log_manager import configure_logging
from stonks.scanner.filters import scan_stocks


def main() -> None:
    """Run the STONKS scanner."""

    configure_logging()

    print("=== STONKS Scanner ===")

    results = scan_stocks()

    print("\n=== RESULTS ===")

    if not results:
        print("No matching stocks found.")
        return

    for quote in results:
        print(quote)


if __name__ == "__main__":
    main()
