# =============================================================================
# File: test_position.py
# Purpose: Pytest file for test_position.py.
# =============================================================================

from stonks.journal.position import Position


def test_create_position() -> None:
    """Verify a position can be created before persistence."""

    position = Position(
        ticker="NVDA",
        strategy="Momentum",
        catalyst="Positive earnings",
    )

    assert position.position_id is None
    assert position.ticker == "NVDA"
    assert position.strategy == "Momentum"
    assert position.catalyst == "Positive earnings"
    assert position.entry_reason == ""
    assert position.notes == ""


def test_position_annotations() -> None:
    """Verify trade reflections are preserved."""

    position = Position(
        ticker="TEST",
        entry_reason="Breakout above resistance",
        exit_reason="Momentum faded",
        mistakes="Entered too early",
        lessons_learned="Wait for confirmation",
    )

    assert position.entry_reason == "Breakout above resistance"
    assert position.exit_reason == "Momentum faded"
    assert position.mistakes == "Entered too early"
    assert position.lessons_learned == "Wait for confirmation"
