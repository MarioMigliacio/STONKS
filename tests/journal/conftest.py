# =============================================================================
# File: conftest.py
# Purpose: Shared pytest fixtures for journal tests.
# =============================================================================

import pytest

from stonks.journal.journal_database import (
    create_connection,
    initialize_database,
)
from stonks.journal.journal_repository import JournalRepository
from stonks.journal.journal_service import JournalService
from stonks.journal.position import Position


@pytest.fixture
def journal(tmp_path):
    """Provide an initialized journal service and repository."""

    database_path = tmp_path / "test_journal.db"
    initialize_database(database_path)

    connection = create_connection(database_path)

    try:
        repository = JournalRepository(connection)
        service = JournalService(connection)

        with connection:
            position_id = repository.create_position(Position(ticker="AMD"))

        yield service, repository, position_id

    finally:
        connection.close()
