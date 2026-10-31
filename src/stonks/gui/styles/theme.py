# =============================================================================
# File: theme.py
# Purpose: Defines the centralized visual theme for the STONKS GUI.
# =============================================================================

from stonks.gui.styles.cia_dossier_theme import CIA_DOSSIER_THEME
from stonks.gui.styles.cia_mission_theme import CIA_MISSION_THEME
from stonks.gui.styles.cia_sources_theme import CIA_SOURCES_THEME
from stonks.gui.styles.cia_theme import CIA_WORKSPACE_THEME
from stonks.gui.styles.scanner_theme import SCANNER_WORKSPACE_THEME

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
    background: transparent;
}

QLabel#journalPageSubtitle {
    color: #91A2B9;
    font-size: 12px;
    background: transparent;
}

QLabel#journalSectionLabel {
    color: #C4D0E1;
    font-size: 14px;
    font-weight: bold;
}

QLabel#journalAccountLabel {
    color: #A9B5C6;
    font-size: 11px;
    font-weight: bold;
    background: transparent;
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

QPushButton#journalCreateButton {
    background-color: #294F7B;
    border: 1px solid #39699D;
    border-radius: 8px;
    padding: 0px;
    text-align: center;
}

QPushButton#journalCreateButton:hover {
    background-color: #356596;
}

QPushButton#journalCreateButton:pressed {
    background-color: #203E63;
}

QPushButton#journalActionsButton {
    background-color: #344055;
    color: #E8EDF5;
    border: 1px solid #45566F;
    border-radius: 8px;
    padding: 0px;
    text-align: center;
}

QPushButton#journalActionsButton:hover {
    background-color: #43516A;
}

QPushButton#journalActionsButton:pressed {
    background-color: #263244;
}

QPushButton#journalCreateButton:disabled,
QPushButton#journalActionsButton:disabled {
    background-color: #252E3D;
    border-color: #344055;
    color: #778397;
}

QPushButton#journalActionsButton::menu-indicator {
    image: none;
    width: 0px;
    height: 0px;
}

QComboBox#journalAccountSelector {
    background-color: #263244;
    color: #E8EDF5;
    border: 1px solid #42516A;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 13px;
    font-weight: bold;
}

QComboBox#journalAccountSelector:hover {
    background-color: #2B394D;
    border-color: #617B9C;
}

QComboBox#journalAccountSelector:focus {
    border-color: #59A8FF;
}

QComboBox#journalAccountSelector:disabled {
    background-color: #252E3D;
    color: #778397;
    border-color: #344055;
}

QComboBox#journalAccountSelector::drop-down {
    border: none;
    width: 32px;
}

QComboBox#journalAccountSelector QAbstractItemView {
    background-color: #263244;
    color: #E8EDF5;
    border: 1px solid #42516A;
    selection-background-color: #235C93;
    selection-color: #FFFFFF;
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

QLineEdit#journalSearchInput,
QComboBox#journalStatusFilter {
    background-color: #263244;
    color: #E8EDF5;
    border: 1px solid #42516A;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
}

QLineEdit#journalSearchInput:hover,
QComboBox#journalStatusFilter:hover {
    background-color: #2B394D;
    border-color: #617B9C;
}

QLineEdit#journalSearchInput:focus,
QComboBox#journalStatusFilter:focus {
    border-color: #59A8FF;
}

QLineEdit#journalSearchInput {
    selection-background-color: #235C93;
    selection-color: #FFFFFF;
}

QComboBox#journalStatusFilter::drop-down {
    border: none;
    width: 30px;
}

QComboBox#journalStatusFilter QAbstractItemView {
    background-color: #263244;
    color: #E8EDF5;
    border: 1px solid #42516A;
    selection-background-color: #235C93;
    selection-color: #FFFFFF;
}

QLabel#accountMetricsNote {
    color: #8190A5;
    font-size: 11px;
    background: transparent;
}

QDateEdit#journalDateFilter {
    background-color: #263244;
    color: #E8EDF5;
    border: 1px solid #42516A;
    border-radius: 8px;
    padding: 8px 10px;
    selection-background-color: #235C93;
    selection-color: #FFFFFF;
}

QDateEdit#journalDateFilter:hover:enabled {
    background-color: #2B394D;
    border-color: #617B9C;
}

QDateEdit#journalDateFilter:focus {
    border-color: #59A8FF;
}

QDateEdit#journalDateFilter:disabled {
    background-color: #222B39;
    color: #8190A5;
    border-color: #344055;
}

QDateEdit#journalDateFilter::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 30px;
    border: none;
    background: transparent;
}

QDateEdit#journalDateFilter::down-arrow {
    image: url(STONKS_ACCOUNT_CALENDAR_ICON);
    width: 17px;
    height: 17px;
}

QCalendarWidget#accountDateCalendar {
    background-color: #1C2532;
    color: #E8EDF5;
    border: 1px solid #42516A;
}

QCalendarWidget#accountDateCalendar QWidget#qt_calendar_navigationbar {
    background-color: #263346;
    border-bottom: 1px solid #344154;
}

QCalendarWidget#accountDateCalendar QToolButton {
    background: transparent;
    color: #E8EDF5;
    border: none;
    border-radius: 5px;
    padding: 6px;
    font-weight: 600;
}

QCalendarWidget#accountDateCalendar QToolButton:hover {
    background-color: #354761;
}

QCalendarWidget#accountDateCalendar QMenu {
    background-color: #1C2532;
    color: #E8EDF5;
    border: 1px solid #42516A;
}

QCalendarWidget#accountDateCalendar QSpinBox {
    background-color: #263244;
    color: #E8EDF5;
    border: 1px solid #42516A;
    border-radius: 4px;
    padding: 4px;
}

QCalendarWidget#accountDateCalendar QAbstractItemView {
    background-color: #1C2532;
    alternate-background-color: #222D3C;
    color: #E8EDF5;
    selection-background-color: #235C93;
    selection-color: #FFFFFF;
    border: none;
    outline: none;
}

QCalendarWidget#accountDateCalendar QAbstractItemView:enabled:hover {
    background-color: #263C59;
}

QFrame#accountFilterSeparator {
    background-color: #344055;
    border: none;
}

QPushButton#accountClearFiltersLink {
    background: transparent;
    border: none;
    color: #59A8FF;
    padding: 4px 2px;
    text-align: right;
    font-weight: 600;
}

QPushButton#accountClearFiltersLink:hover {
    color: #8CC5FF;
    text-decoration: underline;
}

QPushButton#accountClearFiltersLink:pressed {
    color: #347DC4;
}

QPushButton#accountClearFiltersLink:focus {
    border: none;
    outline: none;
}
"""

# Extend the application's existing theme without changing its established rules.
STONKS_DARK_THEME += SCANNER_WORKSPACE_THEME
STONKS_DARK_THEME += CIA_WORKSPACE_THEME
STONKS_DARK_THEME += CIA_MISSION_THEME
STONKS_DARK_THEME += CIA_SOURCES_THEME
STONKS_DARK_THEME += CIA_DOSSIER_THEME
