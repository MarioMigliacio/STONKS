# =============================================================================
# File: trade_execution.py
# Purpose: Defines an individual trade execution.
# =============================================================================

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from stonks.journal.execution_side import ExecutionSide


@dataclass
class TradeExecution:
    """
    Represents a single filled buy or sell execution.

    Each execution belongs to a trading position. Multiple
    executions may be associated with the same position,
    supporting partial entries and exits.

    Monetary values use Decimal to preserve precision.

    Attributes:
        position_id:
            Identifier of the associated trading position.

        side:
            Direction of the execution (BUY or SELL).

        executed_at:
            Timestamp when the execution occurred.

        shares:
            Number of shares executed, with support for fractional share quantities.

        price:
            Execution price per share.

        execution_id:
            Unique database identifier. None before persistence.

        fees:
            Fees or commissions associated with the execution.

        notes:
            Additional execution-specific observations.
    """

    position_id: int
    side: ExecutionSide
    executed_at: datetime
    shares: Decimal
    price: Decimal

    execution_id: Optional[int] = None

    fees: Decimal = Decimal("0.00")
    notes: str = ""

    @property
    def gross_value(self) -> Decimal:
        """
        Calculate the gross monetary value of the execution.

        Returns:
            Decimal:
                Execution price multiplied by share quantity.
        """
        return self.price * self.shares

    @property
    def net_cash_flow(self) -> Decimal:
        """
        Calculate the signed cash flow of the execution.

        Purchases reduce cash by their gross value plus fees.
        Sales increase cash by their gross value minus fees.

        Returns:
            Decimal:
                Signed cash movement associated with execution.
        """
        if self.side == ExecutionSide.BUY:
            return -(self.gross_value + self.fees)

        if self.side == ExecutionSide.SELL:
            return self.gross_value - self.fees

        raise ValueError(f"Unsupported execution side: {self.side}")
