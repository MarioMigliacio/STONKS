# =============================================================================
# File: position_status.py
# Purpose: Defines the lifecycle status of a trading position.
# =============================================================================

from enum import Enum


class PositionStatus(str, Enum):
    """Represent the lifecycle status of a trading position."""

    DRAFT = "DRAFT"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
