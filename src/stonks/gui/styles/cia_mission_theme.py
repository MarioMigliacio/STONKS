# =============================================================================
# File: cia_mission_theme.py
# Purpose: Styles CIA Mission Brief panels, metrics, and catalyst indicators.
# =============================================================================

CIA_MISSION_THEME = """
QWidget#ciaBriefContainer { background: #101923; }
QFrame#ciaMissionBanner, QFrame#ciaMetricPanel, QFrame#ciaIntelligenceSection {
    background: #192532;
    border: 1px solid #2b3a48;
    border-radius: 10px;
}

QFrame#ciaMetricPanel { min-height: 78px;}
QLabel#ciaTarget {
    color: #f1f5f9;
    font-size: 18px;font-weight: 700;
    background: transparent;
}

QLabel#ciaMissionStatus {
    color: #94a3b8;
    background: #223241;
    border: 1px solid #344859;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 11px;
    font-weight: 700;
}

QLabel#ciaMissionStatus[catalyst="breaking"] {
    color: #f4d58d;
    background: #3a3225;
    border-color: #75623d;
}

QLabel#ciaMissionStatus[catalyst="active"] {
    color: #65d9b5;
    background: #1c3b32;
    border-color: #376b54;
}

QLabel#ciaMetricCaption {
    background: transparent;
    color: #94a3b8;
    font-size: 10px;
    font-weight: 700;
}

QLabel#ciaMetricValue {
    background: transparent;
    color: #f1f5f9;
    font-size: 20px;
    font-weight: 700;
}

QLabel#ciaMetricValue[signal="positive"] { color: #65d9b5; }
QLabel#ciaMetricValue[signal="negative"] { color: #f28b91; }
QLabel#ciaSectionTitle {
    background: transparent;
    color: #f1f5f9;
    font-size: 13px;
    font-weight: 700;
}

QLabel#ciaSectionBody {
    background: transparent;
    color: #c4d0df;
    font-size: 12px;
}
"""
