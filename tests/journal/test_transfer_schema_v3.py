# =============================================================================
# File: test_transfer_schema_v3.py
# Purpose: Pytest file for test_transfer_schema_v3.py.
# =============================================================================

import sqlite3
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from stonks.journal.models.account_type import AccountType
from stonks.journal.models.opening_cash_balance import OpeningCashBalance
from stonks.journal.models.trading_account import TradingAccount
from stonks.journal.persistence.journal_database import (
    SCHEMA_VERSION,
    create_connection,
    get_schema_version,
    initialize_database,
)
from stonks.journal.persistence.opening_cash_repository import OpeningCashRepository
from stonks.journal.services.journal_service import JournalService


def fund_test_accounts(connection, *account_ids):
    """Create opening cash snapshots for accounts used in transfer tests."""
    opening_repo = OpeningCashRepository(connection)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    with connection:
        for account_id in account_ids:
            opening_repo.upsert(
                OpeningCashBalance(
                    account_id=account_id,
                    amount=Decimal("10000"),
                    effective_at=start,
                )
            )


def test_v3_creates_transfer_relationships(tmp_path) -> None:
    """Require parent transfers, linked legs, and strict table typing."""
    path = tmp_path / "journal.db"
    initialize_database(path)
    connection = create_connection(path)
    try:
        assert get_schema_version(connection) == SCHEMA_VERSION == 3
        tables = {row["name"]: row for row in connection.execute("PRAGMA table_list")}
        assert tables["account_transfers"]["strict"] == 1
        assert tables["account_transactions"]["strict"] == 1
        cols = {row["name"] for row in connection.execute("PRAGMA table_info(account_transactions)")}
        assert "transfer_id" in cols
        assert any(
            row["from"] == "transfer_id" and row["table"] == "account_transfers"
            for row in connection.execute("PRAGMA foreign_key_list(account_transactions)")
        )
    finally:
        connection.close()


def test_transfer_is_paired_and_balanced(tmp_path) -> None:
    """Persist both linked legs without changing consolidated cash."""
    path = tmp_path / "journal.db"
    initialize_database(path)
    connection = create_connection(path)
    try:
        service = JournalService(connection)
        source = service.create_trading_account(TradingAccount("Cash", AccountType.CASH))
        destination = service.create_trading_account(TradingAccount("IRA", AccountType.ROTH_IRA))
        fund_test_accounts(connection, source, destination)
        outgoing_id, incoming_id = service.create_account_transfer(
            source, destination, Decimal("125.25"), datetime.now(timezone.utc)
        )
        legs = connection.execute(
            "SELECT * FROM account_transactions WHERE transaction_id IN (?, ?)",
            (outgoing_id, incoming_id),
        ).fetchall()
        assert len(legs) == 2
        assert legs[0]["transfer_id"] == legs[1]["transfer_id"]
        assert legs[0]["transfer_id"] is not None
        assert {leg["transaction_type"] for leg in legs} == {"TRANSFER_IN", "TRANSFER_OUT"}
        assert sum(
            Decimal(leg["amount"]) * (1 if leg["transaction_type"] == "TRANSFER_IN" else -1) for leg in legs
        ) == Decimal("0")
        with pytest.raises(ValueError, match="independently"):
            service.delete_account_transaction(outgoing_id)
    finally:
        connection.close()


def test_v3_rejects_missing_or_duplicate_transfer_leg(tmp_path) -> None:
    """Enforce non-null pairing and at most one leg of each direction."""
    path = tmp_path / "journal.db"
    initialize_database(path)
    connection = create_connection(path)
    try:
        service = JournalService(connection)
        source = service.create_trading_account(TradingAccount("Cash", AccountType.CASH))
        destination = service.create_trading_account(TradingAccount("IRA", AccountType.ROTH_IRA))
        fund_test_accounts(connection, source, destination)
        outgoing, incoming = service.create_account_transfer(
            source, destination, Decimal("15"), datetime.now(timezone.utc)
        )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """INSERT INTO account_transactions
                   (account_id, transaction_type, occurred_at, amount)
                   VALUES (?, 'TRANSFER_IN', ?, '15')""",
                (destination, datetime.now(timezone.utc).isoformat()),
            )
        connection.rollback()
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """INSERT INTO account_transactions
                   (account_id, transaction_type, transfer_id, occurred_at, amount)
                   VALUES (?, 'TRANSFER_IN', ?, ?, '15')""",
                (
                    destination,
                    connection.execute(
                        "SELECT transfer_id FROM account_transactions WHERE transaction_id = ?", (incoming,)
                    ).fetchone()[0],
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
        connection.rollback()
        assert outgoing != incoming
    finally:
        connection.close()


def test_provisional_v3_fails_closed(tmp_path) -> None:
    """Reject old v3 databases that lack the parent transfer table."""
    path = tmp_path / "old.db"
    connection = create_connection(path)
    try:
        with connection:
            connection.execute("CREATE TABLE account_transactions (transaction_id INTEGER PRIMARY KEY)")
            connection.execute("PRAGMA user_version = 3")
    finally:
        connection.close()
    with pytest.raises(RuntimeError, match="Provisional schema v3"):
        initialize_database(path)
