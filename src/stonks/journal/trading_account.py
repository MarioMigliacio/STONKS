# =============================================================================
# File: trading_account.py
# Purpose: Defines the trading account data model.
# =============================================================================

from dataclasses import dataclass
from typing import Optional

from stonks.journal.account_type import AccountType


@dataclass
class TradingAccount:
    """
    Represent a brokerage account tracked by the trading journal.

    Attributes:
        name:
            User-defined display name for the trading account.
        account_type:
            Classification of the brokerage account.
        broker:
            Name of the brokerage provider.
        account_id:
            Database-generated unique account identifier.
        is_active:
            Whether the account accepts new journal activity.
        is_default:
            Whether the account is the preferred account for new entries.
    """

    name: str
    account_type: AccountType
    broker: str = ""
    account_id: Optional[int] = None
    is_active: bool = True
    is_default: bool = False
