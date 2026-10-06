# =============================================================================
# File: test_journal_backup.py
# Purpose: Pytest file for test_journal_backup.py.
# =============================================================================


import pytest

from stonks.journal.journal_backup import (
    create_database_backup,
)
from stonks.journal.journal_database import (
    SCHEMA_VERSION,
    create_connection,
    get_schema_version,
    initialize_database,
)


def test_create_database_backup(tmp_path) -> None:
    """Verify a journal database backup is created."""

    database_path = tmp_path / "test_journal.db"
    backup_directory = tmp_path / "backups"

    initialize_database(database_path)

    backup_path = create_database_backup(
        database_path=database_path,
        backup_directory=backup_directory,
    )

    assert backup_path.exists()
    assert backup_path.is_file()
    assert backup_path.parent == backup_directory
    assert backup_path.suffix == ".db"


def test_backup_preserves_journal_data(tmp_path) -> None:
    """Verify a backup contains the source journal records."""

    database_path = tmp_path / "test_journal.db"
    backup_directory = tmp_path / "backups"

    initialize_database(database_path)

    connection = create_connection(database_path)

    try:
        with connection:
            connection.execute(
                """
                INSERT INTO positions (ticker)
                VALUES (?)
                """,
                ("AMD",),
            )

    finally:
        connection.close()

    backup_path = create_database_backup(
        database_path=database_path,
        backup_directory=backup_directory,
    )

    backup_connection = create_connection(backup_path)

    try:
        row = backup_connection.execute(
            """
            SELECT ticker
            FROM positions
            """
        ).fetchone()

        assert row is not None
        assert row["ticker"] == "AMD"

    finally:
        backup_connection.close()


def test_backup_preserves_schema_version(tmp_path) -> None:
    """Verify a backup preserves the journal schema version."""

    database_path = tmp_path / "test_journal.db"
    backup_directory = tmp_path / "backups"

    initialize_database(database_path)

    backup_path = create_database_backup(
        database_path=database_path,
        backup_directory=backup_directory,
    )

    backup_connection = create_connection(backup_path)

    try:
        assert get_schema_version(backup_connection) == SCHEMA_VERSION

    finally:
        backup_connection.close()


def test_missing_database_cannot_be_backed_up(
    tmp_path,
) -> None:
    """Verify a missing source database is rejected."""

    database_path = tmp_path / "missing.db"
    backup_directory = tmp_path / "backups"

    with pytest.raises(
        FileNotFoundError,
        match="Journal database does not exist",
    ):
        create_database_backup(
            database_path=database_path,
            backup_directory=backup_directory,
        )

    assert not database_path.exists()


def test_multiple_backups_are_unique(tmp_path) -> None:
    """Verify repeated backups do not overwrite each other."""

    database_path = tmp_path / "test_journal.db"
    backup_directory = tmp_path / "backups"

    initialize_database(database_path)

    first_backup = create_database_backup(
        database_path=database_path,
        backup_directory=backup_directory,
    )

    second_backup = create_database_backup(
        database_path=database_path,
        backup_directory=backup_directory,
    )

    assert first_backup != second_backup
    assert first_backup.exists()
    assert second_backup.exists()
