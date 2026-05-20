from stonks.scanner.filters import scan_stocks


def main():
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