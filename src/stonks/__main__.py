# =============================================================================
# File: __main__.py
# Purpose: Entry point for running STONKS as a Python module.
# ============================================================================= 

from stonks.scanner.filters import scan_stocks


def main():
    """Run the STONKS scanner."""
    
    print("=== STONKS Scanner ===")

    results = scan_stocks()

    print("\n=== RESULTS ===")

    if not results:
        print("No matching stocks found.")
        return

    for stock in results:
        print(stock)


if __name__ == "__main__":
    main()
