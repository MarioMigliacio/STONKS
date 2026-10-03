# =============================================================================
# File: test_journal_storage.py
# Purpose: Pytest file for test_journal_storage.py.
# =============================================================================

import csv

import pytest

from stonks.journal.journal_storage import (
    atomic_write_csv,
)


def test_atomic_write_creates_csv(tmp_path) -> None:
    """Verify a new CSV is written correctly."""

    file_path = tmp_path / "orders.csv"

    atomic_write_csv(
        file_path,
        ["id", "ticker"],
        [[1, "AAPL"], [2, "TSLA"]],
    )

    with file_path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        rows = list(csv.reader(file))

    assert rows == [
        ["id", "ticker"],
        ["1", "AAPL"],
        ["2", "TSLA"],
    ]


def test_atomic_write_replaces_csv(tmp_path) -> None:
    """Verify replacement removes old records."""

    file_path = tmp_path / "orders.csv"
    file_path.write_text(
        "id,ticker\n1,OLD\n",
        encoding="utf-8",
    )

    atomic_write_csv(
        file_path,
        ["id", "ticker"],
        [[2, "NEW"]],
    )

    assert file_path.read_text(
        encoding="utf-8",
    ).splitlines() == [
        "id,ticker",
        "2,NEW",
    ]


def test_atomic_write_preserves_original_on_error(
    tmp_path,
) -> None:
    """Verify invalid records do not replace existing data."""

    file_path = tmp_path / "orders.csv"
    original = "id,ticker\n1,ORIGINAL\n"

    file_path.write_text(
        original,
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        atomic_write_csv(
            file_path,
            ["id", "ticker"],
            [[2, "NEW", "EXTRA"]],
        )

    assert (
        file_path.read_text(
            encoding="utf-8",
        )
        == original
    )
