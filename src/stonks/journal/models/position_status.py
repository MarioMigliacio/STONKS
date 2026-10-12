# =============================================================================
# File: position_status.py
# Purpose: Represents lifecycle status of a position position.
# =============================================================================

from enum import Enum


class PositionStatus(str, Enum):
    """Represent the lifecycle status of a trading position."""

    DRAFT = "DRAFT"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
