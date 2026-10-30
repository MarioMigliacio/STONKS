# =============================================================================
# File: scanner_theme.py
# Purpose: Defines scoped visual styling for the Scanner workspace foundation.
# =============================================================================

# Scanner Workspace palette for programmatic table-value coloring.
SCANNER_POSITIVE_COLOR = "#65D9B5"
SCANNER_NEGATIVE_COLOR = "#F28B91"

# Scanner Workspace QSS. Object-name selectors keep these rules scoped to ScannerPage.
SCANNER_WORKSPACE_THEME = """
QWidget#scannerWorkspace {
    background: #101923; color: #edf3f8;
}

QLabel#scannerEyebrow, QLabel#scannerKicker {
    color: #65d9b5; font-size: 10px; font-weight: 700;
}

QLabel#scannerTitle {
    color: #f1f5f9; font-size: 24px; font-weight: 700;
    }

QLabel#scannerSubtitle, QLabel#scannerHint, QLabel#scannerMetricCaption {
    color: #94a3b8; font-size: 11px;
}

QLabel#scannerSectionTitle {
    color: #f1f5f9; font-size: 14px; font-weight: 700;
}

QLabel#scannerMetricValue {
    color: #f1f5f9; font-size: 21px; font-weight: 700;
}

QLabel#scannerStateValue {
    color: #65d9b5; font-size: 21px; font-weight: 700;
}

QLabel#scannerStatus {
    color: #b9c9d5; font-size: 12px;
}

QFrame#scannerPanel, QFrame#scannerMetric {
    background: #192532; border: 1px solid #2b3a48; border-radius: 10px;
}

QFrame#scannerStrategyCard {
    background: #223241; border: 1px solid #344859; border-radius: 7px;
}

QCheckBox#scannerStrategyCheck {
    color: #f1f5f9; font-weight: 600; spacing: 10px;
}

QCheckBox#scannerStrategyCheck::indicator {
    width: 17px; height: 17px;
}

QComboBox#scannerMatchMode {
    color: #f1f5f9; background: #223241; border: 1px solid #3a5062;
    border-radius: 6px; padding: 7px 12px; min-width: 145px;
}

QComboBox#scannerMatchMode:disabled {
    color: #738496; 
}

QComboBox#scannerMatchMode QAbstractItemView {
    color: #f1f5f9; background: #223241; selection-background-color: #285c59;
}

QPushButton#scannerRunButton {
    color: #102521; background: #65d9b5; border: 1px solid #65d9b5;
    border-radius: 7px; padding: 9px 18px; font-weight: 700;
}

QPushButton#scannerRunButton:hover {
    background: #82e8c9;
}

QPushButton#scannerRunButton:disabled {
    background: #354e4b; border-color: #354e4b; color: #8aa9a2;
}

QPushButton#scannerCancelButton {
    color: #dce7ef; background: transparent; border: 1px solid #526474;
    border-radius: 7px; padding: 9px 18px; font-weight: 600;
}

QPushButton#scannerCancelButton:hover {
    background: #293a48;
}

QPushButton#scannerCancelButton:disabled {
    color: #718393; border-color: #344452;
}

QTableWidget#scannerResults {
    color: #e4edf4; background: #192532; alternate-background-color: #1e2c39;
    gridline-color: #2c3e4d; border: 0px; selection-background-color: #2a4853;
    selection-color: #ffffff;
}

QTableWidget#scannerResults QHeaderView::section {
    color: #a9bac8; background: #223241; border: 0px;
    border-bottom: 1px solid #3a4e5e; padding: 9px 6px; font-weight: 700;
}

QTableWidget#scannerResults QTableCornerButton::section {
    background: #223241; 
}

QWidget#scannerWorkspace QLabel {
    background-color: transparent;
    border: none;
}

QFrame#scannerPanel QLabel,
QFrame#scannerMetric QLabel,
QFrame#scannerStrategyCard QLabel {
    background-color: transparent;
    border: none;
}

QCheckBox#scannerStrategyCheck {
    background-color: #223241;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 9px 12px;
    spacing: 12px;
    min-height: 24px;
}

QCheckBox#scannerStrategyCheck[selected="true"] {
    background-color: #27443f;
    border: 1px solid #65d9b5;
}

QCheckBox#scannerStrategyCheck::indicator {
    width: 17px;
    height: 17px;
    border: 1px solid #8093a4;
    border-radius: 3px;
    background: #172431;
}

QCheckBox#scannerStrategyCheck::indicator:checked {
    background: #65d9b5;
    border-color: #65d9b5;
}

QPushButton#scannerModeButton {
    color: #aebdca;
    background: #223241;
    border: 1px solid #3a5062;
    border-radius: 6px;
    padding: 8px 16px;
    text-align: center;
    font-weight: 700;
    min-width: 52px;
}

QPushButton#scannerModeButton:checked {
    background: #285c59;
    color: #e7fff5;
    border-color: #65d9b5;
}

QPushButton#scannerModeButton:hover:enabled {
    background: #35665f;
}

QPushButton#scannerModeButton:disabled {
    color: #738496;
    background: #1c2b36;
    border-color: #30414f;
}

QTableWidget#scannerResults {
    qproperty-horizontalScrollMode: ScrollPerPixel;
}
"""
