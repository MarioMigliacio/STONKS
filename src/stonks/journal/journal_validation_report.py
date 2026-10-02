# =============================================================================
# File: journal_validation_report.py
# Purpose: Generates read-only validation reports for journal data.
#
# Notes:
# - Loads existing journal records through the storage layer.
# - Uses journal_validator.py for integrity checks.
# - Does not modify or repair historical records.
# =============================================================================

import logging

from stonks.journal.journal_storage import load_orders
from stonks.journal.journal_validator import (
    validate_orders,
    validate_position_balances,
    validate_positions,
)
from stonks.log_manager import configure_logging

logger = logging.getLogger(__name__)


def print_validation_results(
    category: str,
    warnings: list[str],
) -> None:
    """
    Display validation results for a specific category.

    Args:
        category:
            Name of the validation category.

        warnings:
            Validation warning messages to display.

    Returns:
        None.
    """
    print("")
    print(f"=== {category} ===")

    if not warnings:
        print("PASS - No issues detected.")
        return

    for warning in warnings:
        print(f"WARNING - {warning}")

    print(f"Total warnings: {len(warnings)}")


def run_validation_report() -> None:
    """
    Load journal records and display an integrity report.

    Executes order-level, position-balance, and chronological
    position validation against the existing CSV records.

    The report is read-only and does not modify journal data.

    Returns:
        None.
    """
    logger.info("Starting journal validation report.")

    orders = load_orders()

    print("")
    print("========================================")
    print("       STONKS JOURNAL VALIDATION")
    print("========================================")
    print(f"Orders loaded: {len(orders)}")

    order_warnings = validate_orders(orders)
    balance_warnings = validate_position_balances(orders)
    position_warnings = validate_positions(orders)

    print_validation_results(
        "ORDER VALIDATION",
        order_warnings,
    )

    print_validation_results(
        "POSITION BALANCES",
        balance_warnings,
    )

    print_validation_results(
        "POSITION INTEGRITY",
        position_warnings,
    )

    total_warnings = len(order_warnings) + len(balance_warnings) + len(position_warnings)

    print("")
    print("========================================")
    print(f"TOTAL WARNINGS: {total_warnings}")
    print("========================================")

    logger.info(
        "Journal validation completed with %d warnings.",
        total_warnings,
    )


def main() -> None:
    """
    Run the journal validation command-line utility.

    Configures application logging and generates the
    journal integrity report.

    Returns:
        None.
    """
    configure_logging()
    run_validation_report()


if __name__ == "__main__":
    main()
