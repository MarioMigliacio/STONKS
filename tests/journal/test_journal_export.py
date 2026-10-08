# =============================================================================
# File: test_journal_export.py
# Purpose: Pytest file for test_journal_export.py.
# =============================================================================

import csv
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from stonks.journal.execution_side import ExecutionSide
from stonks.journal.journal_database import (
    create_connection,
    initialize_database,
)
from stonks.journal.journal_export import (
    export_journal_to_csv,
)
from stonks.journal.journal_repository import JournalRepository
from stonks.journal.trade_execution import TradeExecution


def test_export_creates_all_journal_csv_files(
    tmp_path,
) -> None:
    """Verify all journal tables are exported to CSV."""

    database_path = tmp_path / "journal.db"
    export_directory = tmp_path / "exports"

    initialize_database(database_path)

    export_path = export_journal_to_csv(
        database_path=database_path,
        export_directory=export_directory,
    )

    assert export_path.exists()
    assert export_path.is_dir()

    assert (export_path / "positions.csv").exists()

    assert (export_path / "trade_executions.csv").exists()

    assert (export_path / "account_transactions.csv").exists()


def test_export_preserves_position_data(
    tmp_path,
) -> None:
    """Verify persisted position data is exported correctly."""

    database_path = tmp_path / "journal.db"
    export_directory = tmp_path / "exports"

    initialize_database(database_path)

    connection = create_connection(database_path)

    try:
        with connection:
            connection.execute(
                """
                INSERT INTO positions (
                    ticker,
                    strategy,
                    notes
                )
                VALUES (?, ?, ?)
                """,
                (
                    "NVDA",
                    "Momentum",
                    "Clean breakout setup",
                ),
            )

    finally:
        connection.close()

    export_path = export_journal_to_csv(
        database_path=database_path,
        export_directory=export_directory,
    )

    with (export_path / "positions.csv").open(
        "r",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert len(rows) == 1
    assert rows[0]["ticker"] == "NVDA"
    assert rows[0]["strategy"] == "Momentum"
    assert rows[0]["notes"] == "Clean breakout setup"


def test_empty_tables_include_csv_headers(
    tmp_path,
) -> None:
    """Verify empty journal tables still export headers."""

    database_path = tmp_path / "journal.db"
    export_directory = tmp_path / "exports"

    initialize_database(database_path)

    export_path = export_journal_to_csv(
        database_path=database_path,
        export_directory=export_directory,
    )

    with (export_path / "positions.csv").open(
        "r",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        rows = list(csv.reader(csv_file))

    assert len(rows) == 1
    assert "position_id" in rows[0]
    assert "ticker" in rows[0]


def test_missing_database_cannot_be_exported(
    tmp_path,
) -> None:
    """Verify export rejects a missing journal database."""

    database_path = tmp_path / "missing.db"
    export_directory = tmp_path / "exports"

    with pytest.raises(
        FileNotFoundError,
        match="Journal database does not exist",
    ):
        export_journal_to_csv(
            database_path=database_path,
            export_directory=export_directory,
        )

    assert not database_path.exists()


def test_export_preserves_execution_values(
    tmp_path,
) -> None:
    """
    Verify execution precision and timestamps survive CSV export.
    """

    database_path = tmp_path / "journal.db"
    export_directory = tmp_path / "exports"

    initialize_database(database_path)

    connection = create_connection(database_path)

    try:
        repository = JournalRepository(connection)

        position_id = connection.execute(
            """
            INSERT INTO positions (ticker)
            VALUES (?)
            """,
            ("AMD",),
        ).lastrowid

        repository.create_execution(
            TradeExecution(
                position_id=position_id,
                side=ExecutionSide.BUY,
                executed_at=datetime(
                    2026,
                    10,
                    6,
                    15,
                    30,
                    tzinfo=timezone.utc,
                ),
                shares=Decimal("1.375"),
                price=Decimal("123.4567"),
                fees=Decimal("0.25"),
                notes="Fractional entry",
            )
        )

        connection.commit()

    finally:
        connection.close()

    export_path = export_journal_to_csv(
        database_path=database_path,
        export_directory=export_directory,
    )

    with (export_path / "trade_executions.csv").open(
        "r",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert len(rows) == 1

    execution = rows[0]

    assert execution["side"] == "BUY"
    assert execution["shares"] == "1.375"
    assert execution["price"] == "123.4567"
    assert execution["fees"] == "0.25"
    assert execution["executed_at"] == ("2026-10-06T15:30:00+00:00")


def test_export_preserves_special_characters(
    tmp_path,
) -> None:
    """
    Verify CSV export safely preserves special characters.
    """

    database_path = tmp_path / "journal.db"
    export_directory = tmp_path / "exports"

    initialize_database(database_path)

    special_notes = 'Bought breakout, then thought "YOLO".\nThis was probably a terrible idea.'

    connection = create_connection(database_path)

    try:
        with connection:
            connection.execute(
                """
                INSERT INTO positions (
                    ticker,
                    notes
                )
                VALUES (?, ?)
                """,
                (
                    "NVDA",
                    special_notes,
                ),
            )

    finally:
        connection.close()

    export_path = export_journal_to_csv(
        database_path=database_path,
        export_directory=export_directory,
    )

    with (export_path / "positions.csv").open(
        "r",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert len(rows) == 1
    assert rows[0]["notes"] == special_notes
