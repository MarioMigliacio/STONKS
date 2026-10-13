# =============================================================================
# File: conftest.py
# Purpose: Shared pytest fixtures for journal tests.
# =============================================================================

import pytest

from stonks.journal.models.account_type import AccountType
from stonks.journal.models.position import Position
from stonks.journal.models.trading_account import TradingAccount
from stonks.journal.persistence.journal_database import (
    create_connection,
    initialize_database,
)
from stonks.journal.persistence.journal_repository import JournalRepository
from stonks.journal.services.journal_service import JournalService


@pytest.fixture
def journal(tmp_path):
    """
    Provide an initialized journal service and repository.

    Creates a temporary schema v2 database with a default
    trading account and an associated test position.
    """
    database_path = tmp_path / "test_journal.db"
    initialize_database(database_path)

    connection = create_connection(database_path)

    try:
        repository = JournalRepository(connection)
        service = JournalService(connection)

        account_id = service.create_trading_account(
            TradingAccount(
                name="Test Roth IRA",
                account_type=AccountType.ROTH_IRA,
                broker="Webull",
            )
        )

        position_id = service.create_position(
            Position(
                ticker="AMD",
                account_id=account_id,
            )
        )

        yield service, repository, position_id

    finally:
        connection.close()
