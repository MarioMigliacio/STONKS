# =============================================================================
# File: journal_storage.py
# Purpose: Provides persistence functionality for the STONKS journal subsystem.
#
# Notes:
# - Responsible for loading and saving journal data.
# - Does NOT perform analytics.
# - Does NOT calculate trading statistics.
# - Analytics belong in journal_analyzer.py.
# =============================================================================

import csv
from pathlib import Path

from stonks.journal.trade_order import TradeOrder
from stonks.journal.account_snapshot import AccountSnapshot

# =============================================================================
# Journal Data Paths
# =============================================================================

DATA_DIRECTORY = Path("data/journal")

ORDERS_FILE = DATA_DIRECTORY / "orders.csv"
SNAPSHOTS_FILE = DATA_DIRECTORY / "account_snapshots.csv"

# =============================================================================
# Directory Helpers
# =============================================================================

def ensure_journal_directory_exists():
    """
    Create the journal data directory if it does not already exist.
    """

    DATA_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True
    )

# =============================================================================
# Trade Order Persistence
# =============================================================================

def save_order(order: TradeOrder):
    """
    Append a TradeOrder to orders.csv.
    """

    ensure_journal_directory_exists()

    file_has_content = ORDERS_FILE.exists() and ORDERS_FILE.stat().st_size > 0

    with open(
        ORDERS_FILE,
        mode="a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        if not file_has_content:
            writer.writerow([
                "order_id",
                "position_id",
                "trade_date",
                "ticker",
                "order_type",
                "fill_price",
                "shares",
                "order_total",
                "time_issued",
                "notes"
            ])

        writer.writerow([
            order.order_id,
            order.position_id,
            order.trade_date,
            order.ticker,
            order.order_type,
            order.fill_price,
            order.shares,
            order.order_total,
            order.time_issued,
            order.notes
        ])

def load_orders() -> list[TradeOrder]:
    """
    Load all TradeOrder records from orders.csv.
    """

    if not ORDERS_FILE.exists():
        return []

    orders = []

    with open(
        ORDERS_FILE,
        mode="r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            orders.append(
                TradeOrder(
                    order_id=int(row["order_id"]),
                    position_id=int(row["position_id"]),
                    trade_date=row["trade_date"],
                    ticker=row["ticker"],
                    order_type=row["order_type"],
                    fill_price=float(row["fill_price"]),
                    shares=int(row["shares"]),
                    order_total=float(row["order_total"]),
                    time_issued=row["time_issued"],
                    notes=row["notes"]
                )
            )

    return orders

# =============================================================================
# Account Snapshot Persistence
# =============================================================================

def save_snapshot(snapshot: AccountSnapshot):
    """
    Append an AccountSnapshot to account_snapshots.csv.
    """

    ensure_journal_directory_exists()

    file_has_content = SNAPSHOTS_FILE.exists() and SNAPSHOTS_FILE.stat().st_size > 0

    with open(
        SNAPSHOTS_FILE,
        mode="a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        if not file_has_content:
            writer.writerow([
                "snapshot_date",
                "account_value_before",
                "account_value_after",
                "notes"
            ])

        writer.writerow([
            snapshot.snapshot_date,
            snapshot.account_value_before,
            snapshot.account_value_after,
            snapshot.notes
        ])

def load_snapshots() -> list[AccountSnapshot]:
    """
    Load all AccountSnapshot records from account_snapshots.csv.
    """

    if not SNAPSHOTS_FILE.exists():
        return []

    snapshots = []

    with open(
        SNAPSHOTS_FILE,
        mode="r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            snapshots.append(
                AccountSnapshot(
                    snapshot_date=row["snapshot_date"],
                    account_value_before=float(
                        row["account_value_before"]
                    ),
                    account_value_after=float(
                        row["account_value_after"]
                    ),
                    notes=row["notes"]
                )
            )

    return snapshots