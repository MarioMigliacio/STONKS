# =============================================================================
# File: test_journal_backup.py
# Purpose: Pytest file for test_journal_backup.py.
# =============================================================================


import sqlite3

import pytest

from stonks.journal.journal_backup import (
    create_database_backup,
    restore_database_backup,
    validate_database_backup,
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


def test_valid_database_backup_passes_validation(
    tmp_path,
) -> None:
    """Verify a valid journal backup passes validation."""

    database_path = tmp_path / "test_journal.db"
    backup_directory = tmp_path / "backups"

    initialize_database(database_path)

    backup_path = create_database_backup(
        database_path=database_path,
        backup_directory=backup_directory,
    )

    validate_database_backup(backup_path)


def test_missing_backup_fails_validation(
    tmp_path,
) -> None:
    """Verify a missing backup cannot be validated."""

    backup_path = tmp_path / "missing.db"

    with pytest.raises(
        FileNotFoundError,
        match="Journal backup does not exist",
    ):
        validate_database_backup(backup_path)


def test_non_database_backup_fails_validation(
    tmp_path,
) -> None:
    """Verify a non-SQLite file cannot be restored."""

    backup_path = tmp_path / "fake_backup.db"

    backup_path.write_text("Definitely a journal database. Trust me.")

    with pytest.raises(
        ValueError,
        match="not a valid SQLite database",
    ):
        validate_database_backup(backup_path)


def test_unrelated_database_fails_validation(
    tmp_path,
) -> None:
    """Verify an unrelated SQLite database is rejected."""

    backup_path = tmp_path / "unrelated.db"

    connection = sqlite3.connect(str(backup_path))

    try:
        with connection:
            connection.execute(
                """
                CREATE TABLE pokemon (
                    name TEXT NOT NULL
                )
                """
            )

    finally:
        connection.close()

    with pytest.raises(
        ValueError,
        match="required journal tables",
    ):
        validate_database_backup(backup_path)


def test_wrong_schema_version_fails_validation(
    tmp_path,
) -> None:
    """Verify an incompatible journal schema is rejected."""

    database_path = tmp_path / "test_journal.db"
    backup_directory = tmp_path / "backups"

    initialize_database(database_path)

    backup_path = create_database_backup(
        database_path=database_path,
        backup_directory=backup_directory,
    )

    connection = create_connection(backup_path)

    try:
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION + 1}")

    finally:
        connection.close()

    with pytest.raises(
        ValueError,
        match="does not match supported version",
    ):
        validate_database_backup(backup_path)


def test_restore_database_backup(tmp_path) -> None:
    """Verify a journal database can be restored from backup."""

    database_path = tmp_path / "journal.db"
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

    connection = create_connection(database_path)

    try:
        with connection:
            connection.execute(
                """
                DELETE FROM positions
                """
            )

            connection.execute(
                """
                INSERT INTO positions (ticker)
                VALUES (?)
                """,
                ("NVDA",),
            )

    finally:
        connection.close()

    restore_database_backup(
        backup_path=backup_path,
        database_path=database_path,
        backup_directory=backup_directory,
    )

    connection = create_connection(database_path)

    try:
        rows = connection.execute(
            """
            SELECT ticker
            FROM positions
            ORDER BY ticker
            """
        ).fetchall()

        assert [row["ticker"] for row in rows] == ["AMD"]

    finally:
        connection.close()


def test_restore_creates_safety_backup(
    tmp_path,
) -> None:
    """Verify restore preserves the current journal first."""

    database_path = tmp_path / "journal.db"
    backup_directory = tmp_path / "backups"

    initialize_database(database_path)

    original_backup = create_database_backup(
        database_path=database_path,
        backup_directory=backup_directory,
    )

    connection = create_connection(database_path)

    try:
        with connection:
            connection.execute(
                """
                INSERT INTO positions (ticker)
                VALUES (?)
                """,
                ("NVDA",),
            )

    finally:
        connection.close()

    safety_backup = restore_database_backup(
        backup_path=original_backup,
        database_path=database_path,
        backup_directory=backup_directory,
    )

    assert safety_backup.exists()
    assert safety_backup != original_backup

    connection = create_connection(safety_backup)

    try:
        row = connection.execute(
            """
            SELECT ticker
            FROM positions
            WHERE ticker = ?
            """,
            ("NVDA",),
        ).fetchone()

        assert row is not None
        assert row["ticker"] == "NVDA"

    finally:
        connection.close()


def test_invalid_backup_does_not_modify_journal(
    tmp_path,
) -> None:
    """Verify invalid restore input leaves the journal unchanged."""

    database_path = tmp_path / "journal.db"
    backup_directory = tmp_path / "backups"
    invalid_backup = tmp_path / "invalid.db"

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

    invalid_backup.write_text("shadow clone gone terribly wrong")

    with pytest.raises(ValueError):
        restore_database_backup(
            backup_path=invalid_backup,
            database_path=database_path,
            backup_directory=backup_directory,
        )

    connection = create_connection(database_path)

    try:
        row = connection.execute(
            """
            SELECT ticker
            FROM positions
            WHERE ticker = ?
            """,
            ("AMD",),
        ).fetchone()

        assert row is not None

    finally:
        connection.close()


def test_restore_requires_existing_journal(
    tmp_path,
) -> None:
    """Verify restore cannot target a missing journal database."""

    source_database = tmp_path / "source.db"
    missing_database = tmp_path / "missing.db"
    backup_directory = tmp_path / "backups"

    initialize_database(source_database)

    backup_path = create_database_backup(
        database_path=source_database,
        backup_directory=backup_directory,
    )

    with pytest.raises(
        FileNotFoundError,
        match="Journal database does not exist",
    ):
        restore_database_backup(
            backup_path=backup_path,
            database_path=missing_database,
            backup_directory=backup_directory,
        )

    assert not missing_database.exists()
