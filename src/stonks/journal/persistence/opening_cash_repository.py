# =============================================================================
# File: opening_cash_repository.py
# Purpose: Persist and retrieve dated opening cash snapshots.
# =============================================================================

import sqlite3
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from stonks.journal.models.opening_cash_balance import OpeningCashBalance


class OpeningCashRepository:
    """Persist account opening cash snapshots through a shared connection.

    Transaction boundaries are the caller's responsibility.

    Attributes:
        m_connection:
            SQLite connection owned by the journal context.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.m_connection = connection

    def get(self, account_id: int) -> Optional[OpeningCashBalance]:
        """Retrieve an account's opening snapshot, if configured.

        Args:
            account_id:
                Tracked trading account identifier.

        Returns:
            Optional[OpeningCashBalance]:
                Saved snapshot or None when no baseline is recorded.
        """
        row = self.m_connection.execute(
            """
            SELECT account_id, amount, effective_at
            FROM account_opening_cash
            WHERE account_id = ?
            """,
            (account_id,),
        ).fetchone()
        if row is None:
            return None
        return OpeningCashBalance(
            account_id=row["account_id"],
            amount=Decimal(row["amount"]),
            effective_at=datetime.fromisoformat(row["effective_at"]),
        )

    def upsert(self, opening: OpeningCashBalance) -> None:
        """Save a snapshot without automatically committing other journal work.

        Args:
            opening:
                Account cash snapshot to persist.

        Raises:
            ValueError:
                If the amount, account, or date is invalid.
        """
        if type(opening.account_id) is not int or opening.account_id <= 0:
            raise ValueError("A valid trading account ID is required.")
        if not isinstance(opening.amount, Decimal) or not opening.amount.is_finite() or opening.amount < 0:
            raise ValueError("Opening cash must be a finite, non-negative Decimal.")
        if not isinstance(opening.effective_at, datetime) or opening.effective_at.tzinfo is None:
            raise ValueError("Opening cash timestamp must be timezone-aware.")
        if opening.effective_at.utcoffset() is None:
            raise ValueError("Opening cash timestamp must have a UTC offset.")

        row = self.m_connection.execute(
            "SELECT is_active FROM trading_accounts WHERE account_id = ?",
            (opening.account_id,),
        ).fetchone()
        if row is None:
            raise ValueError("Trading account does not exist.")
        if row["is_active"] != 1:
            raise ValueError("Cannot change opening cash for an archived account.")

        normalized_date = opening.effective_at.astimezone(timezone.utc).isoformat()
        self.m_connection.execute(
            """
            INSERT INTO account_opening_cash (account_id, amount, effective_at)
            VALUES (?, ?, ?)
            ON CONFLICT(account_id)
            DO UPDATE SET amount = excluded.amount,
                          effective_at = excluded.effective_at
            """,
            (opening.account_id, str(opening.amount), normalized_date),
        )
