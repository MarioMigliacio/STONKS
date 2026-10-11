# =============================================================================
# File: account_type.py
# Purpose: Defines supported account types.
# =============================================================================

from enum import Enum


class AccountType(str, Enum):
    """Identify the classification of a brokerage account."""

    ROTH_IRA = "ROTH_IRA"
    TRADITIONAL_IRA = "TRADITIONAL_IRA"
    CASH = "CASH"
    MARGIN = "MARGIN"
    OTHER = "OTHER"
