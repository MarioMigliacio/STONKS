# =============================================================================
# File: position.py
# Purpose: Defines a journal trading position.
# =============================================================================

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Position:
    """
    Represents a single trading opportunity in the journal.

    A position groups related buy and sell executions and stores
    the strategy, reasoning, and observations associated with
    the overall trade.

    Financial metrics and position status are derived from
    related executions rather than stored in this model.

    Attributes:
        ticker:
            Stock symbol associated with the position.

        opened_at:
            Timestamp when the position was opened.

        position_id:
            Unique database identifier. None for positions
            that have not yet been persisted.

        strategy:
            Trading setup or strategy used.

        catalyst:
            News or event motivating the trade.

        entry_reason:
            Explanation for entering the position.

        exit_reason:
            Explanation for exiting the position.

        mistakes:
            Mistakes identified during the trade.

        lessons_learned:
            Observations and lessons from the trade.

        notes:
            Additional trading notes.
    """

    ticker: str
    opened_at: datetime

    position_id: Optional[int] = None

    strategy: str = ""
    catalyst: str = ""

    entry_reason: str = ""
    exit_reason: str = ""

    mistakes: str = ""
    lessons_learned: str = ""

    notes: str = ""
