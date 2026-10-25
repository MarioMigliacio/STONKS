# =============================================================================
# File: test_scanner_page.py
# Purpose: Validate scanner workspace selection and presentation behavior.
# =============================================================================

from PySide6.QtTest import QSignalSpy

from stonks.gui.pages.scanner_page import ScannerPage
from stonks.scanner.scanner_match_mode import ScannerMatchMode


def test_initial_controls_require_selection(qtbot):
    """Ensure a scan cannot start without a selected strategy."""
    page = ScannerPage([("standard", "Standard Market Scanner")])
    qtbot.addWidget(page)

    assert not page.m_run_button.isEnabled()
    assert not page.m_cancel_button.isEnabled()

    page.m_strategy_checkboxes["standard"].setChecked(True)
    assert page.m_run_button.isEnabled()


def test_run_emits_selected_strategy_ids_and_match_mode(qtbot):
    """Ensure the workspace emits configuration without executing work."""
    page = ScannerPage(
        [
            ("standard", "Standard Market Scanner"),
            ("future", "Future Scanner"),
        ]
    )
    qtbot.addWidget(page)
    page.m_strategy_checkboxes["standard"].setChecked(True)
    page.m_match_mode.setCurrentIndex(1)
    spy = QSignalSpy(page.run_requested)

    page.m_run_button.click()

    assert spy.count() == 1
    assert spy.at(0)[0] == ["standard"]
    assert spy.at(0)[1] == ScannerMatchMode.ALL


def test_running_state_locks_selection_and_enables_cancel(qtbot):
    """Ensure active execution prevents changes to scanner configuration."""
    page = ScannerPage([("standard", "Standard Market Scanner")])
    qtbot.addWidget(page)
    page.m_strategy_checkboxes["standard"].setChecked(True)
    cancel_spy = QSignalSpy(page.cancel_requested)

    page.set_running(True)
    assert not page.m_run_button.isEnabled()
    assert not page.m_match_mode.isEnabled()
    assert not page.m_strategy_checkboxes["standard"].isEnabled()
    assert page.m_cancel_button.isEnabled()

    page.m_cancel_button.click()
    assert cancel_spy.count() == 1

    page.set_running(False)
    assert page.m_run_button.isEnabled()
    assert not page.m_cancel_button.isEnabled()


def test_rejects_duplicate_strategy_identifiers(qtbot):
    """Ensure selection keys cannot silently overwrite another scanner."""
    import pytest

    with pytest.raises(ValueError, match="unique"):
        ScannerPage([("standard", "One"), ("standard", "Two")])
