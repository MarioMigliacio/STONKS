# =============================================================================
# File: journal_cli.py
# Purpose: Provides command-line tools for entering STONKS journal data.
#
# Notes:
# - Handles user input and validation.
# - Creates TradeOrder objects.
# - Delegates persistence to journal_storage.py.
# =============================================================================

from datetime import date, datetime

from stonks.journal.account_snapshot import AccountSnapshot
from stonks.journal.journal_storage import save_order, save_snapshot
from stonks.journal.trade_order import TradeOrder
from stonks.log_manager import configure_logging

# =============================================================================
# Input Helpers
# =============================================================================


def prompt_string(message: str, allow_empty: bool = False) -> str:
    """Prompt user for a string value."""

    while True:
        value = input(message).strip()

        if value or allow_empty:
            return value

        print("Value cannot be empty.")


def prompt_int(message: str) -> int:
    """Prompt user for an integer value."""

    while True:
        value = input(message).strip()

        try:
            return int(value)

        except ValueError:
            print("Invalid integer. Please try again.")


def prompt_float(message: str) -> float:
    """Prompt user for a floating point value."""

    while True:
        value = input(message).strip()

        try:
            return float(value)

        except ValueError:
            print("Invalid number. Please try again.")


def prompt_order_type() -> str:
    """Prompt user for BUY or SELL."""

    while True:
        order_type = input("Order Type (BUY/SELL): ").strip().upper()

        if order_type in ["BUY", "SELL"]:
            return order_type

        print("Order type must be BUY or SELL.")


# =============================================================================
# Journal Entry Workflow
# =============================================================================


def add_trade_order():
    """Prompt user for trade order details and save the order."""

    print("")
    print("=== Add Trade Order ===")
    print("")

    order_id = prompt_int("Order ID: ")
    position_id = prompt_int("Position ID: ")

    trade_date = prompt_string(f"Trade Date [{date.today()}]: ", allow_empty=True)

    if not trade_date:
        trade_date = str(date.today())

    ticker = prompt_string("Ticker: ").upper()
    order_type = prompt_order_type()
    fill_price = prompt_float("Fill Price: ")
    shares = prompt_int("Shares: ")

    order_total = round(fill_price * shares, 2)

    time_issued = prompt_string(f"Time Issued [{datetime.now().strftime('%H:%M:%S')}]: ", allow_empty=True)

    if not time_issued:
        time_issued = datetime.now().strftime("%H:%M:%S")

    notes = prompt_string("Notes: ", allow_empty=True)

    order = TradeOrder(
        order_id=order_id,
        position_id=position_id,
        trade_date=trade_date,
        ticker=ticker,
        order_type=order_type,
        fill_price=fill_price,
        shares=shares,
        order_total=order_total,
        time_issued=time_issued,
        notes=notes,
    )

    save_order(order)

    print("")
    print("Trade order saved.")
    print(
        f"{order.ticker} | "
        f"{order.order_type} | "
        f"{order.shares} shares @ ${order.fill_price:.2f} | "
        f"Total: ${order.order_total:.2f}"
    )


def add_account_snapshot():
    """Prompt user for account snapshot details and save the snapshot."""

    print("")
    print("=== Add Account Snapshot ===")
    print("")

    snapshot_date = prompt_string(f"Snapshot Date [{date.today()}]: ", allow_empty=True)

    if not snapshot_date:
        snapshot_date = str(date.today())

    account_value_before = prompt_float("Account Value Before: ")
    account_value_after = prompt_float("Account Value After: ")
    notes = prompt_string("Notes: ", allow_empty=True)

    snapshot = AccountSnapshot(
        snapshot_date=snapshot_date,
        account_value_before=account_value_before,
        account_value_after=account_value_after,
        notes=notes,
    )

    save_snapshot(snapshot)

    print("")
    print("Account snapshot saved.")
    print(
        f"{snapshot.snapshot_date} | "
        f"Before: ${snapshot.account_value_before:.2f} | "
        f"After: ${snapshot.account_value_after:.2f} | "
        f"Change: ${snapshot.dollar_change:.2f} | "
        f"Change %: {snapshot.percent_change:+.2f}%"
    )


def main():
    """Run the journal command-line interface."""

    configure_logging()

    print("")
    print("=== STONKS Journal ===")
    print("")
    print("1. Add Trade Order")
    print("2. Add Account Snapshot")
    print("")

    choice = prompt_string("Select option: ")

    if choice == "1":
        add_trade_order()
    elif choice == "2":
        add_account_snapshot()
    else:
        print("Invalid option.")


if __name__ == "__main__":
    main()
