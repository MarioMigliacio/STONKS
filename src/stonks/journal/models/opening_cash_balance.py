# =============================================================================
# File: opening_cash_balance.py
# Purpose: Represent an account's dated opening cash snapshot.
# =============================================================================

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class OpeningCashBalance:
    """Represent the cash available at the beginning of recorded history.

    Attributes:
        account_id:
            Identifier of the tracked trading account.
        amount:
            Finite, non-negative cash amount at the snapshot timestamp.
        effective_at:
            Timezone-aware timestamp marking the start of the cash ledger.
    """

    account_id: int
    amount: Decimal
    effective_at: datetime
