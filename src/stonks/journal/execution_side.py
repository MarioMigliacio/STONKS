# =============================================================================
# File: execution_side.py
# Purpose: Defines supported trade execution directions.
# =============================================================================

from enum import Enum


class ExecutionSide(str, Enum):
    """
    Represents the direction of a trade execution.

    Values:
        BUY:
            Shares purchased.

        SELL:
            Shares sold.
    """

    BUY = "BUY"
    SELL = "SELL"
