# =============================================================================
# File: account_transfer.py
# Purpose: Represents a paired movement of funds between tracked accounts.
# =============================================================================

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class AccountTransfer:
    """Represent a single movement between two tracked trading accounts.

    Attributes:
        source_account_id:
            Account from which funds are withdrawn.
        destination_account_id:
            Account receiving the funds.
        amount:
            Positive Decimal amount transferred.
        occurred_at:
            Timezone-aware date and time of the transfer.
        notes:
            Optional description of the movement.
        transfer_id:
            Database-generated identifier shared by its two ledger legs.
    """

    source_account_id: int
    destination_account_id: int
    amount: Decimal
    occurred_at: datetime
    notes: str = ""
    transfer_id: Optional[int] = None
