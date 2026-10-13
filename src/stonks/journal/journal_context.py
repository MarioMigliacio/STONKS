# =============================================================================
# File: journal_context.py
# Purpose: Manage journal dependencies and database connection lifecycle.
# =============================================================================

from pathlib import Path
from typing import Optional

from stonks.journal.persistence.journal_database import (
    create_connection,
    initialize_database,
)
from stonks.journal.persistence.journal_repository import JournalRepository
from stonks.journal.services.journal_service import JournalService


class JournalContext:
    """
    Manage shared journal dependencies for an application session.

    Attributes:
        m_connection:
            SQLite connection owned by this context.

        m_repository:
            Repository used for journal reads and analytics.

        m_service:
            Service used for validated journal operations.
    """

    def __init__(
        self,
        database_path: Optional[Path] = None,
    ) -> None:
        """
        Initialize the journal database and application dependencies.

        Args:
            database_path:
                Optional SQLite database path. Uses the configured
                default location when omitted.
        """
        initialize_database(database_path)

        connection = create_connection(database_path)

        try:
            repository = JournalRepository(connection)
            service = JournalService(connection)
        except Exception:
            connection.close()
            raise

        self.m_connection = connection
        self.m_repository = repository
        self.m_service = service

    def close(self) -> None:
        """Close the journal database connection."""
        self.m_connection.close()

    def __enter__(self) -> "JournalContext":
        """Return this context when entering a managed session."""
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        """Close the database connection when leaving the session."""
        self.close()
