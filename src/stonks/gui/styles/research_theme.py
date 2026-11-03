# =============================================================================
# File: research_theme.py
# Purpose: Provides scoped styling for the Historical Research workspace.
# =============================================================================

RESEARCH_WORKSPACE_THEME = """
QWidget#researchWorkspace {
    background-color: #101923;
    color: #edf3f8;
}

QLabel#researchEyebrow {
    color: #65d9b5;
    font-size: 10px;
    font-weight: 700;
}

QLabel#researchTitle {
    color: #f1f5f9;
    font-size: 24px;
    font-weight: 700;
}

QLabel#researchSubtitle {
    color: #94a3b8;
    font-size: 11px;
}

QLabel#researchSectionTitle {
    color: #f1f5f9;
    font-size: 14px;
    font-weight: 700;
}

QLabel#researchStatus {
    color: #65d9b5;
    background-color: #1c3b32;
    border: 1px solid #376b54;
    border-radius: 7px;
    padding: 7px 12px;
    font-size: 11px;
    font-weight: 700;
}

QLabel#researchStatus[state="running"] {
    color: #f4d58d;
    background-color: #3a3225;
    border-color: #75623d;
}

QLabel#researchStatus[state="failed"] {
    color: #f28b91;
    background-color: #39272d;
    border-color: #75464a;
}

QLabel#researchStatus[state="partial"],
QLabel#researchStatus[state="empty"] {
    color: #f4d58d;
    background-color: #3a3225;
    border-color: #75623d;
}

QFrame#researchPanel, QFrame#researchChartPanel, QFrame#researchMetricsPanel {
    background-color: #192532;
    border: 1px solid #2b3a48;
    border-radius: 10px;
}

QFrame#researchPanel QLabel, QFrame#researchChartPanel QLabel,
QFrame#researchMetricsPanel QLabel {
    background: transparent;
    border: none;
    color: #b9c9d5;
}

QFrame#researchPanel QLabel#researchSectionTitle {
    color: #f1f5f9;
}

QLineEdit#researchTickerInput,
QDateEdit#researchStartDate,
QDateEdit#researchEndDate,
QComboBox#researchSession,
QComboBox#researchInterval {
    color: #f1f5f9;
    background-color: #223241;
    border: 1px solid #3a5062;
    border-radius: 6px;
    padding: 7px 10px;
    min-height: 20px;
}

QLineEdit#researchTickerInput:focus,
QDateEdit#researchStartDate:focus,
QDateEdit#researchEndDate:focus,
QComboBox#researchSession:focus,
QComboBox#researchInterval:focus {
    border-color: #65d9b5;
}

QLineEdit#researchTickerInput:disabled,
QDateEdit#researchStartDate:disabled,
QDateEdit#researchEndDate:disabled,
QComboBox#researchSession:disabled,
QComboBox#researchInterval:disabled {
    color: #738496;
    background-color: #1c2b36;
    border-color: #30414f;
}

QComboBox#researchSession QAbstractItemView,
QComboBox#researchInterval QAbstractItemView {
    color: #f1f5f9;
    background-color: #223241;
    selection-background-color: #285c59;
}

QPushButton#researchAnalyzeButton {
    color: #102521;
    background-color: #65d9b5;
    border: 1px solid #65d9b5;
    border-radius: 7px;
    padding: 9px 18px;
    font-weight: 700;
}

QPushButton#researchAnalyzeButton:hover:enabled {
    background-color: #82e8c9;
}

QPushButton#researchAnalyzeButton:disabled {
    color: #8aa9a2;
    background-color: #354e4b;
    border-color: #354e4b;
}

QPushButton#researchRefreshButton {
    color: #dce7ef;
    background-color: transparent;
    border: 1px solid #526474;
    border-radius: 7px;
    padding: 9px 18px;
    font-weight: 600;
}

QPushButton#researchRefreshButton:hover:enabled {
    background-color: #293a48;
}

QPushButton#researchRefreshButton:disabled {
    color: #718393;
    border-color: #344452;
}
"""
