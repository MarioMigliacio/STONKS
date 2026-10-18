# =============================================================================
# File: theme.py
# Purpose: Defines the centralized visual theme for the STONKS GUI.
# =============================================================================

STONKS_DARK_THEME = """
QMainWindow {
    background-color: #141A23;
}

QWidget {
    background-color: #141A23;
    color: #E8EDF5;
    font-family: "Segoe UI";
    font-size: 13px;
}

QFrame#navigationSidebar {
    background-color: #1C2532;
    border-right: 1px solid #344154;
}

QFrame#navigationSidebar QLabel {
    background-color: transparent;
}

QLabel#applicationTitle {
    color: #59A8FF;
    font-size: 24px;
    font-weight: bold;
    padding: 12px;
}

QLabel#journalPageTitle {
    color: #E8EDF5;
    font-size: 24px;
    font-weight: bold;
}

QLabel#journalSectionLabel {
    color: #C4D0E1;
    font-size: 14px;
    font-weight: bold;
}

QPushButton {
    background-color: #263346;
    color: #CED7E4;
    border: none;
    border-radius: 6px;
    padding: 12px 16px;
    text-align: left;
}

QPushButton:hover {
    background-color: #354761;
    color: #FFFFFF;
}

QPushButton:checked {
    background-color: #235C93;
    color: #FFFFFF;
    font-weight: bold;
}

QPushButton:focus {
    outline: none;
}

QTableWidget {
    background-color: #141A23;
    alternate-background-color: #1C2532;
    color: #E8EDF5;
    gridline-color: #344154;
    border: 1px solid #344154;
    border-radius: 6px;
    selection-background-color: #235C93;
    selection-color: #FFFFFF;
}

QHeaderView::section {
    background-color: #263346;
    color: #E8EDF5;
    border: none;
    border-right: 1px solid #344154;
    border-bottom: 1px solid #344154;
    padding: 8px 12px;
    font-weight: bold;
}

QTableCornerButton::section {
    background-color: #263346;
    border: none;
}

QTableWidget QTableWidgetItem {
    color: #E8EDF5;
}

QMenu {
    background-color: #171D28;
    color: #E8EDF5;
    border: 1px solid #344055;
    padding: 5px;
}

QMenu::item {
    padding: 8px 24px 8px 12px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #263C59;
    color: #FFFFFF;
}

QMenu::item:disabled {
    color: #778397;
    background-color: transparent;
}

QMenu::separator {
    height: 1px;
    background-color: #45566F;
    margin: 6px 10px;
}

QPushButton#dangerButton {
    background-color: #9F3030;
    color: #FFFFFF;
    border: 1px solid #C84A4A;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: 600;
}

QPushButton#dangerButton:hover {
    background-color: #B93C3C;
}

QPushButton#dangerButton:pressed {
    background-color: #872626;
}

QPushButton#dangerButton:disabled {
    background-color: #48252D;
    color: #A9B5C6;
    border-color: #66363E;
}

QLabel#dangerHeading {
    color: #F8FAFC;
    font-size: 17px;
    font-weight: 600;
}

QLabel#dangerWarning {
    color: #F87171;
    font-weight: 600;
}

QLabel#deletionSummary {
    background-color: #222B3A;
    color: #E8EDF5;
    border: 1px solid #344055;
    border-radius: 6px;
    padding: 12px;
}

QLabel#metricsHeading {
    color: #E8EDF5;
    font-size: 16px;
    font-weight: bold;
}

QFrame#metricCard,
QFrame#metricFooter {
    background-color: #222D3C;
    border: 1px solid #344055;
    border-radius: 9px;
}

QFrame#metricCard {
    min-height: 70px;
}

QLabel#metricCaption {
    color: #A9B5C6;
    font-size: 12px;
    background: transparent;
    border: none;
}

QLabel#metricValue {
    color: #E8EDF5;
    font-size: 22px;
    font-weight: bold;
    background: transparent;
    border: none;
}

QLabel#metricDescription {
    color: #8190A5;
    font-size: 11px;
    background: transparent;
    border: none;
}

QLabel#metricFooterValue {
    color: #E8EDF5;
    font-size: 15px;
    font-weight: bold;
    background: transparent;
    border: none;
}

QLabel#metricValue[performance="profit"] {
    color: #4ADE80;
}

QLabel#metricValue[performance="loss"] {
    color: #F87171;
}

QLabel#positionStatusBadge {
    color: #E8EDF5;
    background-color: #344055;
    border: 1px solid #45566F;
    border-radius: 10px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: bold;
}

QLabel#positionStatusBadge[status="OPEN"] {
    color: #4ADE80;
    background-color: #1C3B32;
    border-color: #376B54;
}

QLabel#positionStatusBadge[status="CLOSED"] {
    color: #E8EDF5;
    background-color: #344055;
    border-color: #45566F;
}

QLabel#positionStatusBadge[status="DRAFT"] {
    color: #A9B5C6;
    background-color: #293344;
}
"""
